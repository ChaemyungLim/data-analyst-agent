
from typing import Dict, List
import psycopg2
import json
from datetime import datetime, timezone

from config.db_settings import DB_CONFIG
from config.redis import redis_client

# 타입 분류
NUMERIC_TYPES = ['integer', 'numeric', 'real', 'double precision', 'smallint', 'bigint']
DATE_TYPES = ['date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone']
TEXT_TYPES = ['character varying', 'varchar', 'text']

# 컬럼 통계 수집 함수
def get_column_stats(cursor, table: str, col: str, dtype: str) -> dict:
    stats = {}
    try:
        if dtype in NUMERIC_TYPES:
            cursor.execute(f"""
                SELECT COUNT(*), COUNT("{col}"), COUNT(DISTINCT "{col}"),
                       MIN("{col}"), MAX("{col}"), AVG("{col}"), STDDEV_POP("{col}"),
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "{col}")
                FROM {table}
            """)
            row = cursor.fetchone()
            stats.update({
                "count": row[0],
                "nulls": row[0] - row[1],
                "distinct": row[2],
                "min": row[3],
                "max": row[4],
                "avg": round(row[5], 3) if row[5] else None,
                "stddev": round(row[6], 3) if row[6] else None,
                "median": row[7]
            })

        elif dtype in DATE_TYPES:
            cursor.execute(f"""
                SELECT COUNT(*), COUNT("{col}"), COUNT(DISTINCT "{col}"),
                       MIN("{col}"), MAX("{col}"),
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM "{col}"))
                FROM {table}
            """)
            row = cursor.fetchone()
            stats.update({
                "count": row[0],
                "nulls": row[0] - row[1],
                "distinct": row[2],
                "min": row[3],
                "max": row[4],
                "median": datetime.fromtimestamp(float(row[5]), tz=timezone.utc).isoformat() if row[5] else None
            })

        elif dtype == 'boolean':
            cursor.execute(f"""
                SELECT COUNT(*), COUNT("{col}"), COUNT(DISTINCT "{col}"),
                       MIN(CASE WHEN "{col}" IS NOT NULL THEN CAST("{col}" AS INT) END),
                       MAX(CASE WHEN "{col}" IS NOT NULL THEN CAST("{col}" AS INT) END)
                FROM {table}
            """)
            row = cursor.fetchone()
            stats.update({
                "count": row[0],
                "nulls": row[0] - row[1],
                "distinct": row[2],
                "min": row[3],
                "max": row[4]
            })

        else:
            cursor.execute(f"""
                SELECT COUNT(*), COUNT("{col}"), COUNT(DISTINCT "{col}")
                FROM {table}
            """)
            row = cursor.fetchone()
            stats.update({
                "count": row[0],
                "nulls": row[0] - row[1],
                "distinct": row[2]
            })

        if dtype in TEXT_TYPES:
            cursor.execute(f"""
                SELECT "{col}", COUNT(*) as freq
                FROM {table}
                GROUP BY "{col}"
                ORDER BY freq DESC
                LIMIT 3
            """)
            top_vals = cursor.fetchall()
            stats["top_values"] = {str(k): v for k, v in top_vals}

        cursor.execute(f"""
            SELECT DISTINCT "{col}"
            FROM {table}
            WHERE "{col}" IS NOT NULL
            LIMIT 3
        """)
        stats["examples"] = [str(row[0]) for row in cursor.fetchall()]

    except Exception as e:
        stats["stats_error"] = str(e)

    return stats

# 전체 스키마 추출 함수
def extract_schema() -> dict:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]
    schema_info = {}

    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table}';
        """)
        columns_raw = cursor.fetchall()
        columns = {}

        for col, dtype, nullable, default in columns_raw:
            col_info = {
                "type": dtype,
                "nullable": (nullable == 'YES'),
                "default": default
            }
            col_info.update(get_column_stats(cursor, table, col, dtype))
            columns[col] = col_info

        # Primary key
        cursor.execute(f"""
            SELECT a.attname FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{table}'::regclass AND i.indisprimary;
        """)
        pk = [r[0] for r in cursor.fetchall()]
        for col in pk:
            if col in columns:
                columns[col]["pk"] = True

        # Unique constraints
        cursor.execute(f"""
            SELECT a.attname FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
            WHERE c.contype = 'u' AND t.relname = '{table}';
        """)
        uq = [r[0] for r in cursor.fetchall()]
        for col in uq:
            if col in columns:
                columns[col]["unique"] = True

        # Foreign keys
        cursor.execute(f"""
            SELECT kcu.column_name, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table}';
        """)
        fk_tuples = cursor.fetchall()
        foreign_keys = []
        for col, ref_table, ref_col in fk_tuples:
            foreign_keys.append((col, ref_table, ref_col))
            if col in columns:
                columns[col]["fk"] = f"{ref_table}.{ref_col}"

        # Check constraints
        cursor.execute(f"""
            SELECT conname, pg_get_expr(conbin, conrelid)
            FROM pg_constraint
            WHERE contype = 'c' AND conrelid = '{table}'::regclass;
        """)
        checks = cursor.fetchall()
        check_constraints = [expr for _, expr in checks]

        schema_info[table] = {
            "columns": columns,
            "primary_key": pk,
            "foreign_keys": foreign_keys,
            "check_constraints": check_constraints
        }
    cursor.close()
    conn.close()
    return schema_info


def generate_edges(schema_info: dict) -> Dict[str, List[str]]:
    edges = {}
    for table, info in schema_info.items():
        for _, ref_table, _ in info.get("foreign_keys", []):
            edges.setdefault(table, []).append(ref_table)
    return edges

def generate_edge_reason(edges: Dict[str, List[str]], schema_info: dict) -> Dict[str, List[dict]]:
    metadata = {}
    for from_table, to_tables in edges.items():
        for to_table in to_tables:
            fk_info = schema_info[from_table].get("foreign_keys", [])
            matched = [fk for fk in fk_info if fk[1] == to_table]
            key = f"{from_table}→{to_table}"
            metadata[key] = []

            for fk_col, ref_table, ref_col in matched:
                col_info = schema_info[from_table]["columns"].get(fk_col, {})
                nullable = col_info.get("nullable", True)
                unique = col_info.get("unique", False)
                pk = col_info.get("pk", False)

                modality = "mandatory" if not nullable else "optional"
                cardinality = "1:1" if unique or pk else "1:N"

                metadata[key].append({
                    "from_column": fk_col,
                    "to_column": ref_col,
                    "cardinality": cardinality,
                    "modality": modality,
                    "reason": f"Linked via {from_table}.{fk_col} → {to_table}.{ref_col}, {cardinality}, {modality} relationship",
                    "source": "auto"
                })
    return metadata

def update_table_relations() -> bool:
    new_schema = extract_schema()
    stored = redis_client.get("table_relations")
    stored_schema = json.loads(stored)["source_schema"] if stored else {}

    if new_schema != stored_schema:
        edges = generate_edges(new_schema)
        edge_reasons = generate_edge_reason(edges, new_schema)

        redis_client.set("table_relations", json.dumps({
            "edges": edges,
            "edge_reasons": edge_reasons,
            "source_schema": new_schema
        }, indent=2, default=str))
        print("Schema updated in Redis.")
        # return True

    print("No schema change detected. Did not update")
    # return False
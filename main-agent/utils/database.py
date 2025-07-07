import psycopg2
import asyncpg
from .config import DB_CONFIG, ASYNC_DB_CONFIG


def get_pg_conn(db_id=None):
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=db_id or DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

async def get_async_pg_conn(db_id=None):
    config = ASYNC_DB_CONFIG.copy()
    if db_id:
        config["database"] = db_id
    return await asyncpg.connect(**config)

def run_postgres_query(db_id: str, sql: str):
    conn = get_pg_conn(db_id)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return rows, column_names
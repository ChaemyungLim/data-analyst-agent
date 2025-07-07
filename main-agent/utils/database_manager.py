import psycopg2
from typing import Dict, List, Optional, Any
from .config import DB_CONFIG, REDIS_CONFIG
import redis
import json


class PostgreSQLManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DB_CONFIG
        self._connection = None
    
    def get_connection(self, db_id: str = None) -> psycopg2.extensions.connection:
        """Get PostgreSQL connection"""
        return psycopg2.connect(**self.config, dbname=db_id or self.config['dbname'])
    
    def execute_query(self, db_id: str, sql: str) -> List[tuple]:
        """Execute SQL query and return results"""
        conn = self.get_connection(db_id)
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            cur.close()
            # print("Successfully executed SQL:", rows)
            return rows, column_names
        finally:
            conn.close()
    
    def get_column_stats(self, cursor, table: str, col: str, dtype: str) -> Dict[str, Any]:
        """Get column statistics for a given table and column"""
        info = {
            'type': dtype,
            'nullable': True,
            'examples': [],
            'distinct_count': 0,
            'null_count': 0,
            'total_count': 0
        }
        
        try:
            # Get basic stats
            cursor.execute(f"""
                SELECT COUNT(*) as total_count,
                       COUNT({col}) as non_null_count,
                       COUNT(DISTINCT {col}) as distinct_count
                FROM {table}
            """)
            result = cursor.fetchone()
            if result:
                info['total_count'] = result[0]
                info['null_count'] = result[0] - result[1]
                info['distinct_count'] = result[2]
            
            # Get examples
            cursor.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 10")
            examples = cursor.fetchall()
            info['examples'] = [row[0] for row in examples]
            
            # Type-specific stats
            if dtype.lower() in ['integer', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double precision']:
                cursor.execute(f"""
                    SELECT MIN({col}) as min_val,
                           MAX({col}) as max_val,
                           AVG({col}) as avg_val,
                           STDDEV({col}) as stddev_val
                    FROM {table}
                    WHERE {col} IS NOT NULL
                """)
                result = cursor.fetchone()
                if result:
                    info.update({
                        'min': result[0],
                        'max': result[1],
                        'avg': result[2],
                        'stddev': result[3]
                    })
            
            elif dtype.lower() in ['date', 'timestamp', 'timestamptz']:
                cursor.execute(f"""
                    SELECT MIN({col}) as min_val,
                           MAX({col}) as max_val
                    FROM {table}
                    WHERE {col} IS NOT NULL
                """)
                result = cursor.fetchone()
                if result:
                    info.update({
                        'min': result[0],
                        'max': result[1]
                    })
            
            elif dtype.lower() in ['varchar', 'text', 'char']:
                cursor.execute(f"""
                    SELECT AVG(LENGTH({col})) as avg_length,
                           MIN(LENGTH({col})) as min_length,
                           MAX(LENGTH({col})) as max_length
                    FROM {table}
                    WHERE {col} IS NOT NULL
                """)
                result = cursor.fetchone()
                if result:
                    info.update({
                        'avg_length': result[0],
                        'min_length': result[1],
                        'max_length': result[2]
                    })
                
                # Get top values
                cursor.execute(f"""
                    SELECT {col}, COUNT(*) as count
                    FROM {table}
                    WHERE {col} IS NOT NULL
                    GROUP BY {col}
                    ORDER BY count DESC
                    LIMIT 5
                """)
                top_values = cursor.fetchall()
                info['top_values'] = [{'value': row[0], 'count': row[1]} for row in top_values]
        
        except Exception as e:
            print(f"Error getting stats for {table}.{col}: {e}")
        
        return info
    
    def extract_schema(self) -> Dict[str, Any]:
        """Extract complete database schema information"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            schema_info = {}
            
            # Get all tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            for table in tables:
                schema_info[table] = {
                    'schema': {
                        'columns': {},
                        'primary_keys': [],
                        'foreign_keys': [],
                        'unique_constraints': [],
                        'check_constraints': []
                    }
                }
                
                # Get column information
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cur.fetchall()
                for col_name, data_type, is_nullable, default in columns:
                    col_stats = self.get_column_stats(cur, table, col_name, data_type)
                    col_stats['nullable'] = is_nullable == 'YES'
                    col_stats['default'] = default
                    schema_info[table]['schema']['columns'][col_name] = col_stats
                
                # Get primary keys
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = 'public' AND table_name = %s
                    AND constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_schema = 'public' AND table_name = %s
                        AND constraint_type = 'PRIMARY KEY'
                    )
                """, (table, table))
                
                primary_keys = [row[0] for row in cur.fetchall()]
                schema_info[table]['schema']['primary_keys'] = primary_keys
                
                # Get foreign keys
                cur.execute("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.constraint_column_usage ccu
                        ON kcu.constraint_name = ccu.constraint_name
                    WHERE kcu.table_schema = 'public' AND kcu.table_name = %s
                    AND kcu.constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_schema = 'public' AND table_name = %s
                        AND constraint_type = 'FOREIGN KEY'
                    )
                """, (table, table))
                
                foreign_keys = []
                for col_name, foreign_table, foreign_col in cur.fetchall():
                    foreign_keys.append({
                        'column': col_name,
                        'references_table': foreign_table,
                        'references_column': foreign_col
                    })
                    # Mark column as foreign key
                    if col_name in schema_info[table]['schema']['columns']:
                        schema_info[table]['schema']['columns'][col_name]['fk'] = {
                            'table': foreign_table,
                            'column': foreign_col
                        }
                
                schema_info[table]['schema']['foreign_keys'] = foreign_keys
            cur.close()
            return schema_info
        finally:
            conn.close()
    

    def generate_edges(self, schema_info: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate table relationship mappings"""
        edges = {}
        
        for table_name, table_info in schema_info.items():
            edges[table_name] = []
            foreign_keys = table_info.get('schema', {}).get('foreign_keys', [])
            
            for fk in foreign_keys:
                referenced_table = fk.get('references_table')
                if referenced_table and referenced_table not in edges[table_name]:
                    edges[table_name].append(referenced_table)
        
        return edges
    
    def generate_edge_reason(self, edges: Dict[str, List[str]], schema_info: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate detailed relationship metadata"""
        edge_reasons = {}
        
        for table_name, related_tables in edges.items():
            edge_reasons[table_name] = []
            
            for related_table in related_tables:
                table_info = schema_info.get(table_name, {})
                foreign_keys = table_info.get('schema', {}).get('foreign_keys', [])
                
                for fk in foreign_keys:
                    if fk.get('references_table') == related_table:
                        reason = {
                            'related_table': related_table,
                            'relationship_type': 'foreign_key',
                            'local_column': fk.get('column'),
                            'foreign_column': fk.get('references_column'),
                            'description': f"{table_name}.{fk.get('column')} references {related_table}.{fk.get('references_column')}"
                        }
                        edge_reasons[table_name].append(reason)
        return edge_reasons
    


class CacheManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or REDIS_CONFIG
        self.client = redis.Redis(**self.config)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with optional expiration"""
        try:
            serialized_value = json.dumps(value, default=str)
            if expire:
                return self.client.setex(key, expire, serialized_value)
            else:
                return self.client.set(key, serialized_value)
        except Exception as e:
            print(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Error checking cache key {key}: {e}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            print(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    def flush_all(self) -> bool:
        """Clear all cache"""
        try:
            return self.client.flushall()
        except Exception as e:
            print(f"Error flushing cache: {e}")
            return False
    
    def get_table_metadata(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table metadata from cache"""
        return self.get(f"metadata:{table_name}")
    
    def set_table_metadata(self, table_name: str, metadata: Dict[str, Any], expire: Optional[int] = 3600) -> bool:
        """Set table metadata in cache"""
        return self.set(f"metadata:{table_name}", metadata, expire)
    
    def get_table_names(self) -> List[str]:
        """Get all table names from cache"""
        try:
            table_names = self.client.smembers("metadata:table_names")
            return [name.decode() if isinstance(name, bytes) else name for name in table_names]
        except Exception as e:
            print(f"Error getting table names: {e}")
            return []
        
    def get_table_relations(self) -> Optional[Dict[str, Any]]:
        """Get table relations from cache"""
        return self.get("table_relations")
    
    def set_table_relations(self, relations: Dict[str, Any], expire: Optional[int] = 3600) -> bool:
        """Set table relations in cache"""
        return self.set("table_relations", relations, expire)
    
    def delete_all_table_metadata(self, table_name: str) -> bool:
        try:
            # Delete all table metadata
            metadata_keys = self.keys("metadata:*")
            for key in metadata_keys:
                self.delete(key)
            
            return True
        except Exception as e:
            print(f"Error invalidating all table metadata: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.client.info()
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}
    
    def check_access(self) -> bool:
        """Check if Redis is accessible"""
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Cache health check failed: {e}")
            return False
    

class MetadataManager:
    def __init__(self, cache_manager: CacheManager, db_manager: PostgreSQLManager):
        self.cache = cache_manager
        self.db = db_manager


    def generate_table_markdown(self, sub_schema: Dict[str, dict]) -> str:
        """Generate markdown for multiple tables"""
        markdown_parts = []
        
        for table_name, table_info in sub_schema.items():
            metadata = self.extract_metadata(table_name, table_info)
            formatted = self.format_metadata(metadata)
            markdown_parts.append(formatted)
        
        return "\n\n".join(markdown_parts)
    
    def generate_metadata(self, table_name: str, schema: dict) -> dict:
        """Generate AI-enhanced metadata for a table"""
        from utils.llm import call_llm
        from prompts.metadata_prompt import prompt, parser
        
        schema_md = self.generate_table_markdown({table_name: schema})
        result = call_llm(prompt=prompt, parser=parser, variables={"schema": schema_md})
        metadata = result.model_dump()
        metadata["schema"] = schema
        return metadata
    
    def update_metadata(self, table_name: str, schema: dict) -> bool:
        """Update table metadata in cache if changed"""
        new_metadata = self.generate_metadata(table_name, schema)
        stored_metadata = self.get(f"metadata:{table_name}")
        
        if not stored_metadata:
            stored_metadata = {}
        
        if new_metadata["columns"] != stored_metadata.get("columns"):
            self.set(f"metadata:{table_name}", new_metadata)
            self.client.sadd("metadata:table_names", table_name)
            print(f"Metadata updated for table: {table_name}")
            return True
        
        print(f"No metadata change for table: {table_name}")
        return False
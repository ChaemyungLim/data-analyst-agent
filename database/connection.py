"""
Database connection and data retrieval module for PostgreSQL
"""

import psycopg2
import pandas as pd
from typing import Dict, Any, Optional, List
import logging


class DatabaseConnection:
    """Handles PostgreSQL database connections and data retrieval"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.logger.info("Database connection established")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        if not self.connection:
            await self.connect()
        
        try:
            df = pd.read_sql_query(query, self.connection, params=params)
            return df
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        
        df = await self.execute_query(query, (table_name,))
        return df.to_dict('records')
    
    async def get_tables(self) -> List[str]:
        """Get list of available tables"""
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        
        df = await self.execute_query(query)
        return df['table_name'].tolist()
    
    async def get_sample_data(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from a table"""
        query = f"SELECT * FROM {table_name} LIMIT %s"
        return await self.execute_query(query, (limit,))
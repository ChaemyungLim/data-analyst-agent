import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/root/limlab01/llm-masters/llm-masters/.env") # 수정 필요

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "daa",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD") 
}

ASYNC_DB_CONFIG = {
    "host": DB_CONFIG["host"],
    "port": DB_CONFIG["port"],
    "database": DB_CONFIG["dbname"],  # asyncpg는 'database' 키를 사용
    "user": DB_CONFIG["user"],
    "password": DB_CONFIG["password"]
}

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": os.getenv("REDIS_PASSWORD"),
    "decode_responses": True
}
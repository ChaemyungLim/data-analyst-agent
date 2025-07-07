import os

# OpenAI 관련 설정
LLM_CONFIG = {
    "model": "gpt-4",
    "temperatures": 0.3,
    "system_prompt": "너는 데이터베이스 구조를 분석하고 관계를 도식화하는 전문가야."
}

# PostgreSQL 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ecommerce_db",
    "user": "chaemyunglim",
    "password": "chae08140!" # os.getenv("POSTGRES_PASSWORD")  
}

# 캐시 파일 경로
CACHE_PATH = os.path.join(os.path.dirname(__file__), "table_graph.json")
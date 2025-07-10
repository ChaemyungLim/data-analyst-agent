# causal_analysis/nodes/fetch_data.py

import pandas as pd
from typing import Dict
from utils.database import run_postgres_query

def build_fetch_data_node(state: Dict) -> Dict:
    sql_query = state.get("query")
    if not sql_query:
        raise ValueError("No SQL query found in state. Please run generate_sql_query_node first.")

    db_id = state.get("db_id", "default_db")  # 기본값 지정 가능

    try:
        rows, columns = run_postgres_query(db_id=db_id, sql=sql_query)
        df = pd.DataFrame(rows, columns=columns)
        state["df"] = df
        return state
    except Exception as e:
        raise RuntimeError(f"Error fetching data from PostgreSQL: {e}")
# causal_analysis/nodes/fetch_data.py

import pandas as pd
from typing import Dict
from utils.database import Database 
from utils.llm import call_llm
from prompts.causal_agent_prompts import fix_sql_prompt, fix_sql_parser, sql_query_parser
from langchain_core.language_models.chat_models import BaseChatModel
database = Database()

def build_fetch_data_node(llm: BaseChatModel):
    def node(state: Dict) -> Dict:
        sql_query = state["sql_query"]
        parsed_query = state["parsed_query"]
        schema_str = state["table_schema_str"]

        if not sql_query:
            raise ValueError("No SQL query found in state. Please run generate_sql_query_node first.")

        db_id = state["db_id"]
        if not db_id:
            raise ValueError("Missing 'db_id' in state")

        expected_columns = [parsed_query["treatment"], parsed_query["outcome"]] \
             + parsed_query.get("confounders", []) \
             + parsed_query.get("mediators", []) \
             + parsed_query.get("instrumental_variables", [])

        # expected_columns에 'users.is_active'처럼 점(.)이 포함된 경우, SQL 결과에서는 컬럼명이 'is_active'로만 들어올 수 있으므로
        # 실제 컬럼명만 추출해 비교
        expected_columns_base = [col.split('.')[-1] for col in expected_columns]
             
        def run_and_validate_query(sql, db_id, expected_columns_base):
            rows, columns = database.run_query(sql=sql, db_id=db_id)
            df = pd.DataFrame(rows, columns=columns)

            missing = [col for col in expected_columns_base if col not in df.columns]
            if missing:
                raise ValueError(f"Missing expected columns in SQL result: {missing}")
            return df

        try:
            df = run_and_validate_query(sql_query, db_id, expected_columns_base)
        except Exception as e:
            last_error = str(e)
            for _ in range(3): # Retry up to 3 times
                revised_response = call_llm(
                    prompt=fix_sql_prompt,
                    parser=fix_sql_parser,
                    variables={
                        "original_sql": sql_query,
                        "error_message": last_error,
                        "treatment": parsed_query["treatment"],
                        "treatment_expression": parsed_query["treatment_expression"],
                        "treatment_expression_description": parsed_query["treatment_expression_description"],
                        "outcome": parsed_query["outcome"],
                        "outcome_expression": parsed_query["outcome_expression"],
                        "outcome_expression_description": parsed_query["outcome_expression_description"],
                        "main_table": parsed_query["main_table"],
                        "join_tables": parsed_query["join_tables"],
                        "confounders": parsed_query["confounders"],
                        "mediators": parsed_query.get("mediators", []),
                        "instrumental_variables": parsed_query.get("instrumental_variables", []),
                        "additional_notes": parsed_query.get("additional_notes", ""),
                        "table_schemas": schema_str,
                    },
                    llm=llm
                )
                revised_query = revised_response.sql_query
                try:
                    df = run_and_validate_query(revised_query, db_id, expected_columns)
                    state["sql_query"] = revised_query
                    break
                except Exception as second_error:
                    last_error = str(second_error)
            else:
                raise RuntimeError(f"SQL retry also failed: {last_error}")

        state["df_raw"] = df
        return state
    return node
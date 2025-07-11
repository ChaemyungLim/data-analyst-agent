# causal_analysis/nodes/generate_sql_query_node.py
import json
from typing import Dict
from prompts.causal_agent_prompts import sql_generation_prompt, sql_query_parser
from utils.llm import call_llm
from data_prep.metadata import generate_table_markdown
from langchain_core.language_models.chat_models import BaseChatModel
from utils.redis_client import redis_client
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def generate_valid_sql(llm, parsed_query, schema_str):
    response = call_llm(
        prompt=sql_generation_prompt,
        parser=sql_query_parser,
        variables={
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
            "table_schemas": schema_str,
        },
        llm=llm,
    )
    return response.sql_query

def build_generate_sql_query_node(llm: BaseChatModel):
    def node(state: Dict) -> Dict:
        parsed_query = state["parsed_query"]
        if not parsed_query:
            raise ValueError("Missing parsed_info in state")


        # 1. 기본 테이블 수집
        tables = [parsed_query.get("main_table", "")] + parsed_query.get("join_tables", [])
        tables = list(set(filter(None, tables)))
        tables = [t.split()[0] for t in tables]  # alias 제거

        # 2. 추가적으로 필요한 테이블 추출 (table.column 형식에서 table만 추출)
        extra_vars = (
            parsed_query.get("confounders", []) +
            parsed_query.get("mediators", []) +
            parsed_query.get("instrumental_variables", [])
        )

        for var in extra_vars:
            if '.' in var:
                table = var.split('.')[0]
                tables.append(table)

        tables = list(set(tables))  # 중복 제거

        if not tables:
            raise ValueError("No tables specified in parsed_info")

        # Redis에서 메타데이터 수집
        metadata_dict = {}
        for table in tables:
            redis_key = f"metadata:{table}"
            raw = redis_client.get(redis_key)
            if not raw:
                raise ValueError(f"No metadata found in Redis for table: {table}")
            metadata = json.loads(raw)
            schema = metadata.get("schema")
            if not schema:
                raise ValueError(f"No schema found for table: {table}")
            metadata_dict[table] = schema

        # markdown 형태로 변환
        schema_str = generate_table_markdown(metadata_dict)
        sql_query = generate_valid_sql(llm, parsed_query, schema_str)
        
        state["table_schema_str"] = schema_str
        state["sql_query"] = sql_query
        return state
    return node
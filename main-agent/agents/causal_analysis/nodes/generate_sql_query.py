# causal_analysis/nodes/generate_sql_query_node.py

import json
from typing import Dict
from prompts.causal_agent_prompts import sql_generation_prompt, sql_query_parser
from utils.llm import call_llm
from utils.redis_client import redis_client
from data_prep.metadata import generate_table_markdown
from langchain_core.language_models.chat_models import BaseChatModel

def build_generate_sql_query_node(state: Dict, llm: BaseChatModel) -> Dict:
    parsed_info = state.get("parsed_info")
    if not parsed_info:
        raise ValueError("Missing parsed_info in state")

    # main table + join_tables 모두 포함
    tables = [parsed_info.get("main_table", "")] + parsed_info.get("join_tables", [])
    tables = list(set(filter(None, tables)))

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

    # LLM 호출
    response = call_llm(
        prompt=sql_generation_prompt,
        parser=sql_query_parser,
        variables={
            "tables": schema_str,
            "parsed_info": parsed_info
        },
        llm=llm
    )

    sql_query = response.query
    state["query"] = sql_query
    return state
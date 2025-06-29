import json
from ..prompts import selector_template
from ..utils import call_llm, parse_json_from_string, extract_metadata, format_metadata

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/root/limlab01/llm-masters/data-analyst-agent/main-agent/.env")

import redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

# ---------------------------------------------------------------------------
# 테이블 너무 많으면 프롬프트에 넣기 어려움 - RAG 방식으로 1차 필터링하는 걸로 수정해야하지 않을까?
# ---------------------------------------------------------------------------

def selector_node(state):
    """
    Selects the appropriate table and retrieves schema information,
    optionally pruning the schema with LLM if too large.
    """
    db_id = state['db_id']

    # 좀 더 정리 필요
    table_names = redis_client.smembers("metadata:table_names")
    schema_tables = []
    fk_lines = []
    for tablename in sorted(table_names):
        meta_json = redis_client.get(f"metadata:{tablename}")
        if not meta_json:
            continue
        meta = json.loads(meta_json)
        schema_dict = extract_metadata(tablename, meta)
        for fk in meta.get("schema", {}).get("foreign_keys", []):
            from_col, to_table, to_col = fk
            fk_lines.append(f'{tablename}."{from_col}" = {to_table}."{to_col}"')
        schema_tables.append(schema_dict)
    schema_info = "\n\n".join(format_metadata(t) for t in schema_tables)
    fk_info = "\n".join(fk_lines) 

    # print("Schema information extracted:", schema_info)

    return {
        **state,
        'desc_str': schema_info,
        'fk_str': fk_info,
        'extracted_schema': None,
        'pruned': False,
        'send_to': 'decomposer_node'
    }

    # 2. pruning 필요성 판단
    need_prune = schema_info.count("# Table:") > 6 or schema_info.count("(") > 30

    if need_prune:
        print("Schema is too large, pruning...")
        prompt = selector_template.format(
            db_id=db_id,
            desc_str=schema_info,
            fk_str=fk_info,
            query=state['query'],
            evidence=state.get('evidence')
        )
        res = call_llm(prompt)
        try:
            extracted_schema = parse_json_from_string(res)
        except Exception:
            print("Error parsing schema from LLM response:", res)
            extracted_schema = {}

        # pruning 반영
        pruned_tables = []
        for table in schema_tables:
            tname = table['table_name']
            decision = extracted_schema.get(tname, "drop_all")
            if decision == "drop_all":
                continue
            elif decision == "keep_all" or decision == "":
                pruned_tables.append(table)
            elif isinstance(decision, list):
                table_copy = dict(table)  # shallow copy
                table_copy['columns'] = [col for col in table['columns'] if col['name'] in decision]
                pruned_tables.append(table_copy)
        schema_info = "\n\n".join(format_metadata(p) for p in pruned_tables)
    else:
        extracted_schema = {t['table_name']: "keep_all" for t in schema_tables}

    print("Schema pruning needed:", need_prune)
    print("extracted_schema:", extracted_schema)
    print("schema_info:", schema_info)
    return {
        **state,
        'desc_str': schema_info,
        'fk_str': fk_info,
        'extracted_schema': extracted_schema,
        'pruned': need_prune,
        'send_to': 'decomposer_node'
    }

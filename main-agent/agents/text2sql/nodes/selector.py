import json
from typing import Dict, Any
from prompts.text2sql_prompts import selector_template
from utils.llm import call_llm
from utils.parsers import parse_json_from_string
from utils.redis_client import redis_client

from langchain_core.language_models.chat_models import BaseChatModel


def extract_metadata(table_name: str, table_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary information for a table's schema"""
    schema = table_meta.get('schema', {})
    columns_schema = schema.get('columns', {})
    columns_desc = table_meta.get('columns', {})

    columns = []
    for col, col_schema in columns_schema.items():
        columns.append({
            'name': col,
            'type': col_schema.get('type'),
            'desc': columns_desc.get(col, ''),
            'nullable': col_schema.get('nullable', False),
            'fk': col_schema.get('fk', None),
            'examples': col_schema.get('examples', []),
            'min': col_schema.get('min', None),
            'max': col_schema.get('max', None),
        })

    metadata = {
        'table_name': table_name,
        'description': table_meta.get('description', ''),
        'columns': columns,
        'foreign_keys': schema.get('foreign_keys', []),
    }
    
    if 'sample_usage' in table_meta:
        metadata['sample_usage'] = table_meta['sample_usage']
    
    return metadata


def format_metadata(table_schema: Dict[str, Any]) -> str:
    """Format metadata dict to markdown string for LLM"""
    lines = [f"# Table: {table_schema['table_name']}", "["]
    
    if table_schema.get('description'):
        lines.append(f"  Description: {table_schema['description']}")
        
    for col in table_schema['columns']:
        desc = col.get('desc', col['name'])
        examples = col.get('examples', [])
        min_val, max_val = col.get('min'), col.get('max')

        # Build example string
        ex_str = ""
        if examples and len(examples) > 0:
            shown = [f"'{e}'" if isinstance(e, str) else str(e) for e in examples[:5]]
            ex_str = f" Value examples: [{', '.join(shown)}]."
        
        # Build range string
        range_str = ""
        if min_val is not None or max_val is not None:
            range_str = f" (Range: {min_val} ~ {max_val}.)"

        lines.append(f"  ({col['name']}, {desc}.{ex_str}{range_str}),")
    
    # Remove last comma and close bracket
    if lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]
    lines.append("]")
    
    return "\n".join(lines)


def selector_node(state, llm: BaseChatModel):
    """
    Selects the appropriate table and retrieves schema information,
    optionally pruning the schema with LLM if too large.
    """
    db_id = state['db_id']

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
        res = call_llm(prompt, llm = llm)
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

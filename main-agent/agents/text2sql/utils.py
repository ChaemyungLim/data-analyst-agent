from typing import Union, Any, overload
from langchain_openai import ChatOpenAI
from langchain_core.prompts import BasePromptTemplate
from langchain_core.output_parsers import BaseOutputParser

@overload
def call_llm(prompt: str, parser: None = None, variables: dict = None, model: str = "gpt-4", temperature: float = 0.3) -> str: ...

@overload
def call_llm(prompt: BasePromptTemplate, parser: None = None, variables: dict = None, model: str = "gpt-4", temperature: float = 0.3) -> str: ...

@overload
def call_llm(prompt: BasePromptTemplate, parser: BaseOutputParser, variables: dict, model: str = "gpt-4", temperature: float = 0.3) -> Any: ...


def call_llm(
    prompt: Union[str, BasePromptTemplate],
    parser: BaseOutputParser = None,
    variables: dict = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> Union[str, Any]:
    """
    General-purpose LLM caller supporting:
    - Plain string prompt → str output
    - PromptTemplate → str output
    - PromptTemplate + Parser → structured output (e.g., BaseModel, dict, list)
    """
    llm = ChatOpenAI(model=model, temperature=temperature)

    # Case 1: PromptTemplate with parser
    if isinstance(prompt, BasePromptTemplate) and parser:
        if not variables:
            raise ValueError("PromptTemplate with parser requires input variables.")
        chain = prompt | llm | parser
        return chain.invoke(variables)

    # Case 2: PromptTemplate without parser
    elif isinstance(prompt, BasePromptTemplate):
        if not variables:
            raise ValueError("PromptTemplate requires input variables.")
        chain = prompt | llm
        return chain.invoke(variables).content.strip()

    # Case 3: Plain string prompt
    elif isinstance(prompt, str):
        return llm.invoke(prompt).content.strip()

    else:
        raise TypeError("Prompt must be a string or a BasePromptTemplate.")
    


import json 
import psycopg2
import re
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/root/limlab01/llm-masters/llm-masters/.env")
    
# 나중에 load 하는 코드로 수정
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "daa", # 수정
    "user": "postgres", # 수정
    "password": os.getenv("POSTGRES_PASSWORD") 
}


# ------------------------ DB 유틸 ------------------------
def get_pg_conn(db_id=None):
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=db_id or DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

def run_postgres_query(db_id: str, sql: str):
    conn = get_pg_conn(db_id)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print("successfully executed SQL!:", rows)
    return rows

def extract_metadata(table_name: str, table_meta: dict):
    """
    Extracts summary information for a table's schema, including columns, foreign keys, and description.
    """
    out = {
        'table_name': table_name,
        'description': table_meta.get('description', ''),
        'columns': [],
        'foreign_keys': [],
    }
    schema = table_meta.get('schema', {})
    columns_schema = schema.get('columns', {})
    columns_desc = table_meta.get('columns', {})

    for col, col_schema in columns_schema.items():
        info = {
            'name': col,
            'type': col_schema.get('type'),
            'desc': columns_desc.get(col, ''),
            'nullable': col_schema.get('nullable', False),
            'fk': col_schema.get('fk', None),
            'examples': col_schema.get('examples', []),
            'min': col_schema.get('min', None),
            'max': col_schema.get('max', None),
        }
        out['columns'].append(info)

    out['foreign_keys'] = schema.get('foreign_keys', [])

    if 'sample_usage' in table_meta:
        out['sample_usage'] = table_meta['sample_usage']
    return out


def format_metadata(table_schema: dict) -> str:
    """
    metadata (dict) → markdown string for selector node.
    """
    out = f"# Table: {table_schema['table_name']}\n[\n"
    if 'description' in table_schema and table_schema['description']:
        out += f"  Description: {table_schema['description']}\n"
        
    for col in table_schema['columns']:
        desc = col.get('desc', col['name'])
        examples = col.get('examples', [])
        min_val = col.get('min')
        max_val = col.get('max')

        ex_str = ""
        if examples and isinstance(examples, list) and len(examples) > 0:
            shown = [f"'{e}'" if isinstance(e, str) else str(e) for e in examples[:5]]
            ex_str = f" Value examples: [{', '.join(shown)}]."
        
        range_str = ""
        if min_val is not None or max_val is not None:
            range_str = f" (Range: {min_val} ~ {max_val}.)"

        out += f"  ({col['name']}, {desc}.{ex_str}{range_str}),\n"
    out = out.rstrip(",\n") + "\n]"
    return out

# ------------------------ Output parser ------------------------                           
def parse_sql_from_string(input_string):
    sql_pattern = r'```sql(.*?)```'
    all_sqls = []
    for match in re.finditer(sql_pattern, input_string, re.DOTALL):
        all_sqls.append(match.group(1).strip())
    if all_sqls:
        return all_sqls[-1]
    else:
        return "error: No SQL found in the input string"
    
def parse_json_from_string(res):
    m = re.search(r"```json\s*([\s\S]+?)```", res)
    if not m:
        m = re.search(r"```([\s\S]+?)```", res)
    if m:
        res = m.group(1).strip()
    return json.loads(res)

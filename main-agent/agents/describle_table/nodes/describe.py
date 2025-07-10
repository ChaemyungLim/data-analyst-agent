import json

from prompts.describe_table_prompts import column_description_prompt as prompt, column_description_parser as parser, TableAnalysis
from data_prep.metadata import generate_table_markdown, update_metadata
from utils.llm import call_llm
from utils.redis_client import redis_client
from langchain_core.language_models.chat_models import BaseChatModel

# -------------------------------
# describe_table_node
# -------------------------------
def describe_table(table_name: str, llm: BaseChatModel) -> TableAnalysis:
    try:
        # Redis에서 schema 정보 불러오기
        redis_key = f"metadata:{table_name}"
        raw = redis_client.get(redis_key)
        if not raw:
            raise ValueError(f"Error: No metadata found in Redis for table: {table_name}")
        
        metadata = json.loads(raw)
        schema = metadata.get("schema")
        if not schema:
            raise ValueError(f"Error: No 'schema' field found for table: {table_name}")

        schema_str = generate_table_markdown({table_name: schema})

        response = call_llm(prompt=prompt, parser=parser, 
                            variables={
                                "table_name": table_name,
                                "column_summary": schema_str
                                }
                            , llm=llm)

        return response
    except Exception as e:
        print(f"Error: Failed to describe table '{table_name}': {e}")
        raise

def describe_table_node(state, llm):
    table_name = state["input"]
    analysis = describe_table(table_name, llm = llm)
    return {
        "table_analysis": analysis.model_dump()
    }

    
# -------------------------------
# Test
# -------------------------------
if __name__ == "__main__":
    test_input = "users"

    try:
        result = describe_table(test_input)
        print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"\nError: failed describing table: {str(e)}\n")





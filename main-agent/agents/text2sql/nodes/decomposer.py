from utils.llm import call_llm
from utils.parsers import parse_sql_from_string
from prompts.text2sql_prompts import decompose_template

from langchain_core.language_models.chat_models import BaseChatModel

def decomposer_node(state, llm: BaseChatModel):
    schema_info = state['desc_str']
    fk_info = state['fk_str']
    query = state['query']
    evidence = state.get('evidence')

    prompt = decompose_template.format(
        desc_str=schema_info, fk_str=fk_info, query=query, evidence=evidence
    )
    llm_reply = call_llm(prompt, llm=llm)
    final_sql = parse_sql_from_string(llm_reply)

    return {
        **state,
        'final_sql': final_sql,
        'qa_pairs': llm_reply,
        'send_to': 'refiner_node'
    }
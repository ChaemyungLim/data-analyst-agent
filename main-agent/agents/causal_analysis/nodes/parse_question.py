# causal_analysis/nodes/parse_question.py
import json
from typing import Callable, Dict

from utils.llm import call_llm
from data_prep.metadata import generate_table_markdown
from utils.redis_client import redis_client
from prompts.causal_agent_prompts import parse_query_prompt, parse_query_parser

from langchain_core.runnables import RunnableLambda
from langchain_core.language_models.chat_models import BaseChatModel


def build_parse_question_node(llm: BaseChatModel) -> Callable:
    def _parse_question(state: Dict) -> Dict:
        question = state["input"]

        # Redis에서 저장된 테이블 리스트 불러오기
        table_keys = redis_client.keys("metadata:*")
        table_markdowns = []

        for key in table_keys:
            table_name = key.split(":")[1]
            raw = redis_client.get(key)
            if not raw:
                continue
            metadata = json.loads(raw)
            schema = metadata.get("schema", {})
            markdown = generate_table_markdown({table_name: schema})
            table_markdowns.append(markdown)

        full_markdown = "\n\n".join(table_markdowns)

        result = call_llm(
            prompt=parse_query_prompt,
            parser=parse_query_parser,
            variables={
                "question": question,
                "tables": full_markdown
            },
            llm=llm
        )

        state["parsed_info"] = result.dict()
        return state

    return RunnableLambda(_parse_question)
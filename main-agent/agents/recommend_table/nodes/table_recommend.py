# 수정 필요

import json
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings

from langchain_core.language_models.chat_models import BaseChatModel
from utils.llm import call_llm
from utils.redis_client import redis_client
from prompts.recommend_table_analysis_prompt import prompt, parser

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parents[1] / ".env")


def load_metadata(redis_client, redis_key="metadata") -> list[Document]:
    table_names = redis_client.smembers(f"{redis_key}:table_names")
    documents = []
    for table in table_names:
        raw = redis_client.get(f"{redis_key}:{table}")
        if not raw:
            continue
        try:
            meta = json.loads(raw)
            desc = meta.get("description", "")
            usage = " ".join(meta.get("sample_usage", []))
            doc_text = f"{desc}\nUse Cases: {usage}"
            documents.append(Document(page_content=doc_text, metadata={"table": table}))
        except Exception as e:
            print(f"Error: failed to parse metadata for table {table}: {e}")
    return documents


def get_table_candidates(query: str, k: int = 15, redis_client=redis_client) -> str:
    documents = load_metadata(redis_client)
    vectorstore = FAISS.from_documents(documents, OpenAIEmbeddings())
    top_k_docs = vectorstore.similarity_search(query, k=k)

    lines = []
    for doc in top_k_docs:
        table = doc.metadata['table']
        content = doc.page_content.strip()[:300].replace('\n', ' ')
        lines.append(f"{table}: {content}")
    return "\n".join(lines)


def recommend_tables(state, llm: BaseChatModel):
    objective = state["objective_summary"]
    table_list = get_table_candidates(objective, k=15)

    try:
        response = call_llm(
            prompt=prompt,
            parser=parser,
            variables={
                "objective": objective,
                "tables": table_list,
                "format_instructions": parser.get_format_instructions()
            },
            llm=llm
        )
        state["recommended_tables"] = response.recommended_tables
        state["recommended_method"] = response.analysis_method
    except Exception as e:
        print(f"Error: Failed to parse recommended tables: {e}")
        state["recommended_tables"] = []
        state["recommended_method"] = "No specific method recommended."
    return state
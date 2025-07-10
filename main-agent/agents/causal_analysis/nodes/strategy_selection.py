# nodes/strategy_selection.py

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from langchain_core.language_models.chat_models import BaseChatModel

from utils.llm import call_llm

from prompts.causal_agent_prompts import (
    causal_strategy_prompt,
    strategy_output_parser
)

def build_strategy_selection_node(llm: BaseChatModel) -> RunnableLambda:
    """
    Selects a causal strategy (task, identification method, estimator, refuter) 
    using an LLM based on user question, variables, and data sample.
    """

    def invoke(inputs: Dict[str, Any]) -> Dict[str, Any]:
        parsed_vars = inputs.get("parsed_query", {})
        question = inputs.get("question", "")
        df_sample = inputs.get("df_sample", "")

        prompt_input = {
            "question": question,
            "treatment": parsed_vars.get("treatment", ""),
            "outcome": parsed_vars.get("outcome", ""),
            "confounders": parsed_vars.get("confounders", []),
            "mediators": parsed_vars.get("mediators", []),
            "instrumental_variables": parsed_vars.get("instrumental_variables", []),
            "df_sample": df_sample
        }

        result = call_llm(
            prompt=causal_strategy_prompt,
            parser=strategy_output_parser,
            variables=prompt_input,
            llm=llm
        )

        return {
            **inputs,
            "strategy": result
        }

    return RunnableLambda(invoke)
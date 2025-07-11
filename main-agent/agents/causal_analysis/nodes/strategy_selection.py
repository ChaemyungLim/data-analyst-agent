# nodes/strategy_selection.py

from typing import Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel

from utils.llm import call_llm

from prompts.causal_agent_prompts import (
    causal_strategy_prompt,
    strategy_output_parser
)

def build_strategy_selection_node(llm: BaseChatModel):
    """
    Selects a causal strategy (task, identification method, estimator, refuter) 
    using an LLM based on user question, variables, and data sample.
    """

    def node(state: Dict) -> Dict:
        df_raw = state["df_raw"]
        df_sample = df_raw.head(10).to_csv(index=False) if df_raw is not None else ""
        
        parsed_vars = state["parsed_query"]
        question = state["input"]

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

        state["strategy"] = result
        return state

    return node
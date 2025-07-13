# nodes/generate_answer.py

from typing import Dict
from langchain_core.runnables import RunnableLambda
from langchain_core.language_models.chat_models import BaseChatModel

from utils.llm import call_llm
from prompts.causal_agent_prompts import generate_answer_prompt, generate_answer_parser


def build_generate_answer_node(llm: BaseChatModel) -> RunnableLambda:
    """
    Uses an LLM to generate an interpretable explanation of the causal inference results.
    """

    def invoke(state: Dict) -> Dict:
        strategy = state["strategy"]
        parsed_query = state["parsed_query"]
        estimate = state["causal_estimate"]
        refutation_result = state["refutation_result"]
        label_maps = state["label_maps"]

        if not strategy or not estimate:
            raise ValueError("Missing strategy or causal_estimate")

        # LLM 입력 구성
        llm_input = {
            "treatment": parsed_query["treatment"],
            "treatment_expression": parsed_query["treatment_expression"],
            "treatment_expression_description": parsed_query["treatment_expression_description"],
            "outcome": parsed_query["outcome"],
            "outcome_expression": parsed_query["outcome_expression"],
            "outcome_expression_description": parsed_query["outcome_expression_description"],
            "main_table": parsed_query["main_table"],
            "join_tables": parsed_query["join_tables"],
            "confounders": parsed_query["confounders"],
            "mediators": parsed_query.get("mediators", []),
            "instrumental_variables": parsed_query.get("instrumental_variables", []),
            "additional_notes": parsed_query.get("additional_notes", ""),
            "estimator": strategy.estimator,
            "task": strategy.task,
            "effect_value": estimate.value,
            "refutation_result": refutation_result or "No refutation performed",
            "label_maps": label_maps or {}
        }

        # LLM 호출
        result = call_llm(
            prompt=generate_answer_prompt,
            parser=generate_answer_parser,
            variables=llm_input,
            llm=llm
        )

        state["final_answer"] = result
        state["final_answer"] = result.explanation if hasattr(result, "explanation") else str(result)
        return state

    return RunnableLambda(invoke)
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
        strategy = state.get("strategy")
        estimate = state.get("causal_estimate")
        refutation_result = state.get("refutation_result", None)

        if not strategy or not estimate:
            raise ValueError("Missing strategy or causal_estimate")

        # LLM 입력 구성
        llm_input = {
            "estimator": strategy.estimator,
            "task": strategy.task,
            "effect_value": estimate.value,
            "refutation_result": refutation_result or "No refutation performed",
        }

        # LLM 호출
        result = call_llm(
            prompt=generate_answer_prompt,
            parser=generate_answer_parser,
            variables=llm_input,
            llm=llm
        )

        state["final_answer"] = result
        return state

    return RunnableLambda(invoke)
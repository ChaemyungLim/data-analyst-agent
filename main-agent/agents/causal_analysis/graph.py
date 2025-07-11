# agents/causal_analysis/graph.py
from langgraph.graph import StateGraph, END

from .state import CausalAnalysisState
from .nodes.parse_question import build_parse_question_node
from .nodes.generate_sql_query import build_generate_sql_query_node
from .nodes.fetch_data import build_fetch_data_node
from .nodes.preprocess import build_preprocess_node
from .nodes.strategy_selection import build_strategy_selection_node
from .nodes.dowhy_analysis import build_dowhy_analysis_node
from .nodes.generate_answer import build_generate_answer_node


def generate_causal_analysis_graph(llm):
    graph = StateGraph(CausalAnalysisState)

    # Add nodes
    graph.add_node("parse_question", build_parse_question_node(llm))
    graph.add_node("generate_sql_query", build_generate_sql_query_node(llm))
    graph.add_node("fetch_data", build_fetch_data_node(llm))
    graph.add_node("preprocess", build_preprocess_node())
    graph.add_node("strategy_selection", build_strategy_selection_node(llm))
    graph.add_node("dowhy_analysis", build_dowhy_analysis_node())
    graph.add_node("generate_answer", build_generate_answer_node(llm))

    # Define edges
    graph.set_entry_point("parse_question")
    graph.add_edge("parse_question", "generate_sql_query")
    graph.add_edge("generate_sql_query", "fetch_data")
    graph.add_edge("fetch_data", "preprocess")
    graph.add_edge("preprocess", "strategy_selection")
    graph.add_edge("strategy_selection", "dowhy_analysis")
    graph.add_edge("dowhy_analysis", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()
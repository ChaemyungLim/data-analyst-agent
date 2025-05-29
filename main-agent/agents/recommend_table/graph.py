from langgraph.graph import StateGraph, START, END
from .state import RecommendState
from .nodes.input_router import set_input_type, route_input_type, parse_document
from .nodes.objective_summary import extract_objective_summary
from .nodes.table_recommend import recommend_tables
from .nodes.erd import generate_erd


def generate_table_recommendation_graph():
    graph = StateGraph(RecommendState)

    graph.add_node("set_input_node", set_input_type)
    graph.add_node("parse_document_node", parse_document)
    graph.add_node("extract_objective_summary_node", extract_objective_summary)
    graph.add_node("recommend_tables_node", recommend_tables)
    graph.add_node("generate_erd_node", generate_erd)

    graph.set_entry_point("set_input_node")

    graph.add_conditional_edges(
        "set_input_node",  
        route_input_type,   # 분기 함수 (노드X)
        {
            "text": "extract_objective_summary_node",
            "document": "parse_document_node"
        }
    )

    graph.add_edge("parse_document_node", "extract_objective_summary_node")
    graph.add_edge("extract_objective_summary_node", "recommend_tables_node")
    graph.add_edge("recommend_tables_node", "generate_erd_node")
    graph.add_edge("generate_erd_node", END)

    return graph.compile()
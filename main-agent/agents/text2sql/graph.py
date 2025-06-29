from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes.selector import selector_node
from .nodes.decomposer import decomposer_node
from .nodes.refiner import refiner_node
from .nodes.review import review_node
from .nodes.system import system_node
    

def router(state: AgentState):
    return state['send_to']

def generate_text2sql_graph():
    graph = StateGraph(AgentState)
    graph.set_entry_point('selector_node') 
    graph.add_node('selector_node', selector_node)
    graph.add_node('decomposer_node', decomposer_node) # task 분해하여 sql 생성
    graph.add_node('refiner_node', refiner_node) # sql 실행 및 에러 해결
    graph.add_node('review_node', review_node)
    graph.add_node('system_node', system_node)

    graph.add_conditional_edges('selector_node', router, {
        'decomposer_node': 'decomposer_node',
    })
    graph.add_conditional_edges('decomposer_node', router, {
        'refiner_node': 'refiner_node',
    })
    graph.add_conditional_edges('refiner_node', router, {
        'review_node': 'review_node',
        'refiner_node': 'refiner_node',
    })

    graph.add_conditional_edges('review_node', router, {
            'refiner_node': 'refiner_node',
            'system_node': 'system_node',
    })

    graph.add_conditional_edges('system_node', lambda s: END, {END: END})
    
    return graph.compile()
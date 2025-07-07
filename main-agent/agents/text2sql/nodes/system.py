def system_node(state):
    print("System_node reached... Generating final output.")
    # print("state:", state)
    return {
        **state,
        'output': {
            'query': state['query'],
            'sql': state.get('pred') or state.get('final_sql'),
            'columns': state.get('columns'),
            'result': state.get('result'),
            'error': state.get('error'),
            'llm_review': state.get('llm_review')
        }
    }
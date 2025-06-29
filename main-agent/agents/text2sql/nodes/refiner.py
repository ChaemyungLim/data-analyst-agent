from ..prompts import refiner_template, refiner_feedback_template
from ..utils import call_llm, parse_sql_from_string, run_postgres_query

def refiner_node(state):
    db_id = state['db_id']
    sql = state.get('pred') or state.get('final_sql')
    llm_review = state.get('llm_review')
    try_times = state.get('try_times', 0)

    if llm_review and try_times == 0:
        error_info = state.get('error', {})
        
        print("Refining SQL with feedback...")
        prompt = refiner_feedback_template.format(
            query=state['query'],
            evidence=state.get('evidence'),
            desc_str=state['desc_str'],
            fk_str=state['fk_str'],
            sql=state['final_sql'],
            review_feedback=llm_review
        )
        
        llm_reply = call_llm(prompt)
        new_sql = parse_sql_from_string(llm_reply)

        return {
            **state,
            'pred': new_sql,
            'try_times': try_times + 1,
            'send_to': 'refiner_node',
            # 'llm_review': None  # 한 번 반영했으니 초기화
        }

    else:
        try:
            print("Executing SQL....")
            result = run_postgres_query(db_id, sql)
            if result and len(result) > 0:
                return {
                    **state,
                    'result': result,
                    'error': None,  # 에러 초기화
                    'send_to': 'review_node'
                }
            else: # 실행은 성공했지만 반환된 결과가 없는 경우
                return {
                    **state,
                    'result': "Sql executed but no rows returned, there might be something wrong with the sql or no data in the table that matches the query.",
                    'error': None,  # 에러 초기화
                    'send_to': 'review_node'
                }
                
        except Exception as e:
            print("Error executing SQL:", e)
            error_info = {'sql': sql, 'error': str(e), 'exception_class': type(e).__name__}

        if try_times >= 3:
            return {
                **state,
                'error': error_info['error'],
                'send_to': 'review_node'
            }
    
        prompt = refiner_template.format(
            query=state['query'],
            evidence=state.get('evidence'),
            desc_str=state['desc_str'],
            fk_str=state['fk_str'],
            sql=error_info['sql'],
            sql_error=error_info.get('error', ''),
            exception_class=error_info.get('exception_class', '')
        )

        llm_reply = call_llm(prompt)
        new_sql = parse_sql_from_string(llm_reply)

        return {
            **state,
            'pred': new_sql,
            'try_times': try_times + 1,
            'send_to': 'refiner_node',
            # 'llm_review': None  # 한 번 반영했으니 초기화
        }
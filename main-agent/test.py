# from agents.describle_table import generate_description_graph
# from agents.recommend_table import generate_table_recommendation_graph
# from agents.text2sql.graph import generate_text2sql_graph
# from prettify import print_final_output_task2, print_final_output_task3, print_final_output_task1

# # task1 test (text2sql)
# input = "user purchases in the last month"
# app = generate_text2sql_graph()

# initial_state = {
#     "query": input,
#     "messages": [],
#     "desc_str": None,
#     "fk_str": None,
#     "extracted_schema": None,
#     "final_sql": None,
#     "qa_pairs": None,
#     "pred": None,
#     "result": None,
#     "error": None,
#     "pruned": False,
#     "send_to": "selector_node",
#     "try_times": 0,
#     "llm_review": None,
#     "review_count": 0,
#     "output": None,
#     "db_id": "daa",  # 필요 시 바꿔주세요
#     "notes": None
# }

# result = app.invoke(initial_state)
# final_output = print_final_output_task1(result["output"])
# print(final_output)


# # task2 test (table description)
# table_name = "users"
# graph = generate_description_graph()
# result = graph.invoke({
#     "input": table_name
# })
# print(print_final_output_task2(result["final_output"]))


# # task3 test (table recommendation)
# app = generate_table_recommendation_graph()
# result = app.invoke({
#     "input": "We want to analyze customer purchasing behavior to identify patterns that lead to higher sales."
# })
# print(print_final_output_task3(result["final_output"]))


# 비동기 실험

import asyncio
from utils.redis_client import async_redis_client
from agents_async.describle_table import generate_description_graph
from agents_async.recommend_table import generate_table_recommendation_graph
from agents_async.text2sql.graph import generate_text2sql_graph
from prettify import print_final_output_task2, print_final_output_task3, print_final_output_task1


async def test():
    try: 
        # task2 test (table description)
        table_name = "users"
        graph = generate_description_graph()
        result = await graph.ainvoke({
            "input": table_name
        })
        print(print_final_output_task2(result["final_output"]))

        # task3 test (table recommendation)
        app = generate_table_recommendation_graph()
        result = await app.ainvoke({
            "input": "I want to test the hypothesis that customers who purchase more frequently also tend to spend more money overall."
        })
        print(print_final_output_task3(result["final_output"]))

        # task1 test (text2sql)
        input = "I want to test the hypothesis that customers who purchase more frequently also tend to spend more money overall."
        app = generate_text2sql_graph()

        initial_state = {
            "query": input,
            "messages": [],
            "desc_str": None,
            "fk_str": None,
            "extracted_schema": None,
            "final_sql": None,
            "qa_pairs": None,
            "pred": None,
            "result": None,
            "error": None,
            "pruned": False,
            "send_to": "selector_node",
            "try_times": 0,
            "llm_review": None,
            "review_count": 0,
            "output": None,
            "db_id": "daa",  # 필요 시 바꿔주세요
            "notes": None
        }

        result = await app.ainvoke(initial_state)
        print(print_final_output_task1(result["output"]))
    finally:
        await async_redis_client.aclose() 

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
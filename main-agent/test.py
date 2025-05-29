from agents.describle_table import generate_description_graph
from agents.recommend_table import generate_table_recommendation_graph
from prettify import print_final_output_task2, print_final_output_task3

# task2 test
table_name = "users"
graph = generate_description_graph()
result = graph.invoke({
    "input": table_name
})
print(print_final_output_task2(result["final_output"]))


# task3 test
app = generate_table_recommendation_graph()
result = app.invoke({
    "input": "We want to analyze customer purchasing behavior to identify patterns that lead to higher sales."
})
print(print_final_output_task3(result["final_output"]))
   

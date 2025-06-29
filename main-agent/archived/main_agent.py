# 여기서 memory 추가 - redis
# 정보 부족하면 더 구체적으로 물어보기
# llm 생성하다가 에러나면 에러 넣어서 다시 한번 생성하도록 -> 에러 처리
# 속도 향상

from agents.describle_table import generate_description_graph
from agents.recommend_table import generate_table_recommendation_graph
# from agents.xxx import generate_xxx_graph
# from agents.xxx import generate_xxx_graph

# 임시로
from test import print_final_output_task2, print_final_output_task3

from langchain_openai import ChatOpenAI
from typing import Literal
import traceback

# ------------------------------
# Agent 타입 결정 함수 (LLM 사용하여 판단하도록 수정 필요)
# ------------------------------
def route_agent(user_input: str) -> Literal["recommend", "describe"]:
    if "want" in user_input:
        return "recommend"
    elif "user" in user_input:
        return "describe"
    else:
        return "etc"  # 예외의 경우 더 물어보도록 설정 max=3회 정도

# ------------------------------
# 대화형 메인 함수
# ------------------------------
def main_agent_loop():
    print("🤖 Hi! How can I assist you? Please enter 'exit' if you want to stop chatting.")

    while True:
        user_input = input("👤 Input: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Have a nice day!")
            break

        try:
            agent_type = route_agent(user_input)

            if agent_type == "recommend":
                app = generate_table_recommendation_graph()
                result = app.invoke({
                    "raw_input": user_input
                })
                print(print_final_output_task3(result["final_output"]))

            elif agent_type == "describe":
                app = generate_description_graph()
                result = app.invoke({
                    "table_name": user_input
                })
                print(print_final_output_task2(result["final_output"]))

            else:
                print("Can you please clarify your request? I can help with table recommendations or descriptions.")
                continue

        except Exception as e:
            print("Error:")
            print(traceback.format_exc())
            print("Try again with a different input or check the table name.")

# ------------------------------
# 실행
# ------------------------------
if __name__ == "__main__":
    main_agent_loop()

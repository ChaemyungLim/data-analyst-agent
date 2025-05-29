import sys
import os
import yaml
import argparse
import json
from dotenv import load_dotenv
from openai import OpenAI

from agents.describle_table import generate_description_graph
from agents.recommend_table import generate_table_recommendation_graph
from prettify import print_final_output_task2, print_final_output_task3

# env 파일 사용 위해 임시로 Chaemyung 디렉토리 경로 설정
sys.path.append(os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

def read_file(path: str) :
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content: str = file.read()
        return content
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def generate(prompt: str):
    try:
        print("Generating response from OpenAI")
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 변경 ?
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=512
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

class Agent:
    def __init__(self, config, user_input, prompt_template_A, prompt_template_path_column_desc_system, prompt_template_path_column_desc_human):
        self.config = config

        self.template_A = self.load_template(prompt_template_A)
        self.template_column_desc_system = self.load_template(prompt_template_path_column_desc_system)
        self.template_column_desc_human = self.load_template(prompt_template_path_column_desc_human)
        self.user_input = user_input
        self.task_list = ["task2", "task3"]
    
    def load_template(self, prompt_template_path) -> str:
        return read_file(prompt_template_path)

    def choose_task(self):
        # 사용자의 입력을 받아 어떤 task, 어떤 table? 분석 할지 고르는 기능
        # llm call로 정하기
        prompt = self.template_A.format(
                user_input = self.user_input,
                task_list = self.task_list
            )

        response = self.ask_openai(prompt) # json 형식으로 나올 수 있도록 프롬프팅

        try:
            cleaned_response = response.strip().strip('`').strip()
            if cleaned_response.startswith('json'):
                cleaned_response = cleaned_response[4:].strip()
            parsed_response = json.loads(cleaned_response)
            chosen_task = parsed_response["chosen_task"].lower()


            if chosen_task == "task2" : # 각 테스크별로 각각 만들어둔 모듈 실행
                print("설명을 원하는 테이블 이름을 입력해주세요")
                while True:
                    table_input = input("👤 Input: ")
                    if table_input.lower() in ["exit", "quit"]:
                        print("Have a nice day!")
                        break
                    app = generate_description_graph()
                    result = app.invoke({
                        "input": f"{table_input}"
                    })
                    print(print_final_output_task2(result["final_output"]))
                    break

            elif chosen_task == "task3" :
                app = generate_table_recommendation_graph()
                result = app.invoke({
                    "input": self.user_input
                })
                print(print_final_output_task3(result["final_output"]))
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse response: {response}. Error: {str(e)}")
            print("assistant", "Choosing Task: I encountered an error in processing. Let me try again.")
            self.choose_task()

        except Exception as e:
            print(f"Error processing response: {str(e)}")
            print("assistant", "I encountered an unexpected error. Let me try a different approach.")
            self.choose_task()
    
    def run_task2():
        """
        input : column desc prompt들 .. + alpha
        output : 파싱된 실행 결과 ?
        """
    
    def execute(self) -> str:
        self.choose_task()
        

    def ask_openai(self, prompt: str) -> str:
        response = generate(prompt)
        return str(response) if response else "No response from OpenAI"


def dict2namespace(config):
    namespace = argparse.Namespace()
    for key, value in config.items():
        if isinstance(value, dict):
            new_value = dict2namespace(value)
        else:
            new_value = value
        setattr(namespace, key, new_value)
    return namespace

def get_user_input():
    print("🤖 Hi! How can I assist you? Please enter 'exit' if you want to stop chatting.")

    while True:
        user_input = input("🧑 Input: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Have a nice day!")
            exit(0)
        return user_input

def run_agent(config,INPUT_DIR,CONFIG_PATH):

    template_path_A = os.path.join(INPUT_DIR, "prompt_A2" + ".txt")
    template_path_column_desc_system = os.path.join(INPUT_DIR, config.prompt_column_desc_system + ".txt")
    template_path_column_desc_human = os.path.join(INPUT_DIR, config.prompt_column_desc_human + ".txt")
    user_input = get_user_input()

    if not os.path.exists(template_path_A):
        raise FileNotFoundError(f"Template file not found: {template_path_column_A}")
    if not os.path.exists(template_path_column_desc_system):
        raise FileNotFoundError(f"Template file not found: {template_path_column_desc_system}")
    if not os.path.exists(template_path_column_desc_human):
        raise FileNotFoundError(f"Template file not found: {template_path_column_desc_human}")

    # output_file = f"{config.experiment_name}.txt"
    # output_path = os.path.join(OUTPUT_DIR, output_file)

    agent = Agent(config, user_input, template_path_A, template_path_column_desc_system, template_path_column_desc_human)
    response = agent.execute() 


if __name__ == "__main__":
    
    INPUT_DIR = "prompts/"
    OUTPUT_DIR = "outputs/"
    CONFIG_PATH = "_config.yml"

    stdout_filename = f"logs/test2.log"
    os.makedirs(f"logs", exist_ok=True)
    logfile = open(stdout_filename, "a", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, logfile) 

    with open(CONFIG_PATH, "r") as f: 
        configs = yaml.safe_load(f)
    config = dict2namespace(configs)

    run_agent(config,INPUT_DIR,CONFIG_PATH)

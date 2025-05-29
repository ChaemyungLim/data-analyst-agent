import sys
import os
import yaml
import argparse
import traceback
import datetime
from typing import Optional

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

def read_file(path: str) -> Optional[str]:
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

def generate(prompt: str) -> Optional[str]:
    try:
        print("Generating response from OpenAI")
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
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
    def __init__(self, config, routing_prompt_path, output_path):
        self.config = config
        self.output_path = output_path
        self.routing_prompt_template = read_file(routing_prompt_path)
        
    def route_agent(self, user_input: str) -> tuple[str, str]:
        if not self.routing_prompt_template:
            return "clarify"
        
        prompt = self.routing_prompt_template.format(user_input=user_input)
        response = generate(prompt)
        print(f"[DEBUG] Routing LLM response: {response}")
        
        if not response:
            return "LLM has no response. Cannot determine task"
        
        answer = response.strip().lower()
        
        if answer.startswith("describe:"):
            table_name = answer.split("describe:")[1].strip()
            return "describe", table_name
        elif answer == "recommend":
            return "recommend", user_input
        else:
            return "clarify", user_input
    
    def run_task(self, task: str, user_input: str):
        if task == "describe":
            app = generate_description_graph()
            result = app.invoke({"input": user_input})
            final_output = result.get("final_output", "[No output generated]")
            final_output = print_final_output_task2(final_output)
            return final_output

        elif task == "recommend":
            app = generate_table_recommendation_graph()
            result = app.invoke({"input": user_input})
            final_output = result.get("final_output", "[No output generated]")
            final_output = print_final_output_task3(final_output)
            return final_output

        else:
            return "Sorry, Could you clarify your question?"
        
    def run_loop(self):
        print("🤖 Hi! How can I assist you? Please type 'exit' to quit.")

        while True:
            user_input = input("Input: ")
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Bye!")
                break

            try:
                task, refined_input = self.route_agent(user_input)
                result = self.run_task(task, refined_input)
                print(result)
                self.log_interaction(user_input, result)
            except Exception:
                print("Error occurred:")
                print(traceback.format_exc())
                continue

    def log_interaction(self, input_text: str, output_text: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] 👤 {input_text}\n")
            f.write(f"[{timestamp}] 🤖 {output_text}\n")

def dict2namespace(config):
    namespace = argparse.Namespace()
    for key, value in config.items():
        if isinstance(value, dict):
            new_value = dict2namespace(value)
        else:
            new_value = value
        setattr(namespace, key, new_value)
    return namespace

def run_agent(config, input_dir, output_dir):
    routing_prompt_path = os.path.join(input_dir, config.prompt_A + ".txt")
    
    if not os.path.exists(routing_prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_template_path}")

    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{config.experiment_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    output_path = os.path.join(output_dir, output_file)

    agent = Agent(config, routing_prompt_path, output_path)
    agent.run_loop()

if __name__ == "__main__":
    
    INPUT_DIR = "prompts/"
    OUTPUT_DIR = "outputs/"
    CONFIG_PATH = "_config_for_test2.yml"

    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logfile = open(log_path, "a", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, logfile)

    with open(CONFIG_PATH, "r") as f:
        config = dict2namespace(yaml.safe_load(f))

    run_agent(config, INPUT_DIR, OUTPUT_DIR)

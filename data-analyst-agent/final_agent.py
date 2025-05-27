import sys
import os
import yaml
import argparse
from dotenv import load_dotenv

# env 파일 사용 위해 임시로 Chaemyung 디렉토리 경로 설정
sys.path.append(os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))


load_dotenv()

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
            model="gpt-4", # 변경 ?
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
    def __init__(self, config, prompt_template_A, prompt_template_path_column_desc_system, prompt_template_path_column_desc_human, output_path):
        self.config = config

        self.template_A = self.load_template(prompt_template_A)
        self.template_column_desc_system = self.load_template(prompt_template_path_column_desc_system)
        self.template_column_desc_human = self.load_template(prompt_template_path_column_desc_human)
    
    def load_template(self, prompt_template_path) -> str:
        return read_file(prompt_template_path)

    def choose_task():
        # 사용자의 입력을 받아 어떤 task, 어떤 table? 분석 할지 고르는 기능
        # llm call로 정하기
        prompt = self.template_A.format(
                
            )

        response = self.ask_openai(prompt) # json 형식으로 나올 수 있도록 프롬프팅

        try:
            cleaned_response = response.strip().strip('`').strip()
            if cleaned_response.startswith('json'):
                cleaned_response = cleaned_response[4:].strip()
            parsed_response = json.loads(cleaned_response)

            if tool_name == "task2" : # 각 테스크별로 각각 만들어둔 모듈 실행
                run_task2()
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response}. Error: {str(e)}")
            self.trace("assistant", "Reasoning A: I encountered an error in processing. Let me try again.")
            self.choose_task()

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            self.trace("assistant", "I encountered an unexpected error. Let me try a different approach.")
            self.choose_task()
    
    def run_task2():
        """
        input : column desc prompt들 .. + alpha
        output : 파싱된 실행 결과 ?
        """
    
    def execute(self) -> str:
        self.choose_task()
        
        return self.messages[-1].content # output으로 뽑아볼 내용 추가

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

def run_agent(config,INPUT_DIR,OUTPUT_DIR,CONFIG_PATH):

    template_path_A = os.path.join(INPUT_DIR, config.prompt_A + ".txt")
    template_path_column_desc_system = os.path.join(INPUT_DIR, config.prompt_column_desc_system + ".txt")
    template_path_column_desc_human = os.path.join(INPUT_DIR, config.prompt_column_desc_human + ".txt")

    if not os.path.exists(template_path_A):
        raise FileNotFoundError(f"Template file not found: {template_path_column_A}")
    if not os.path.exists(template_path_column_desc_system):
        raise FileNotFoundError(f"Template file not found: {template_path_column_desc_system}")
    if not os.path.exists(template_path_column_desc_human):
        raise FileNotFoundError(f"Template file not found: {template_path_column_desc_human}")

    output_file = f"{config.experiment_name}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_file)

    agent = Agent(config, template_path_A, template_path_column_desc_system, template_path_column_desc_human, output_path)
    response = agent.execute() 


if __name__ == "__main__":
    
    INPUT_DIR = "prompts/"
    OUTPUT_DIR = "outputs/"
    CONFIG_PATH = "_config.yml"

    with open(CONFIG_PATH, "r") as f: 
        configs = yaml.safe_load(f)
    config = dict2namespace(configs)

    run_agent(config,INPUT_DIR,OUTPUT_DIR,CONFIG_PATH)

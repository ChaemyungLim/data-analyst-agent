from typing import Union, Any, overload
from langchain_openai import ChatOpenAI
from langchain_core.prompts import BasePromptTemplate
from langchain_core.output_parsers import BaseOutputParser

@overload
def call_llm(prompt: str, parser: None = None, variables: dict = None, model: str = "gpt-4", temperature: float = 0.3) -> str: ...

@overload
def call_llm(prompt: BasePromptTemplate, parser: None = None, variables: dict = None, model: str = "gpt-4", temperature: float = 0.3) -> str: ...

@overload
def call_llm(prompt: BasePromptTemplate, parser: BaseOutputParser, variables: dict, model: str = "gpt-4", temperature: float = 0.3) -> Any: ...



def call_llm(
    prompt: Union[str, BasePromptTemplate],
    parser: BaseOutputParser = None,
    variables: dict = None,
    model: str = "gpt-4",
    temperature: float = 0.3,
) -> Union[str, Any]:
    """
    General-purpose LLM caller supporting:
    - Plain string prompt → str output
    - PromptTemplate → str output
    - PromptTemplate + Parser → structured output (e.g., BaseModel, dict, list)
    """
    llm = ChatOpenAI(model=model, temperature=temperature)

    # Case 1: PromptTemplate with parser
    if isinstance(prompt, BasePromptTemplate) and parser:
        if not variables:
            raise ValueError("PromptTemplate with parser requires input variables.")
        chain = prompt | llm | parser
        return chain.invoke(variables)

    # Case 2: PromptTemplate without parser
    elif isinstance(prompt, BasePromptTemplate):
        if not variables:
            raise ValueError("PromptTemplate requires input variables.")
        chain = prompt | llm
        return chain.invoke(variables).content.strip()

    # Case 3: Plain string prompt
    elif isinstance(prompt, str):
        return llm.invoke(prompt).content.strip()

    else:
        raise TypeError("Prompt must be a string or a BasePromptTemplate.")
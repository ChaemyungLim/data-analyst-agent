from typing import List, Union
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class RecommendedTables(BaseModel):
    table_list: list[str] = Field(...)
    analysis_method: str = Field(...)

parser = PydanticOutputParser(pydantic_object=RecommendedTables)


example = """
"""

system_template =  """
You are a senior data analyst assistant.
You will be provided with a user's business analysis objective and a list of available tables with their descriptions.

Your job is to:
- 1. Understand the user's business analysis intent
- 2. Recommend the most relevant database tables needed to solve the task (up to 10. you don't need to recommend 10 tables). Order them by relevance.
- 3. Describe a detailed analysis process that directly addresses the stated objective
- Your answer will be parsed by a strict JSON parser. Follow the exact output format.

Output Format:
{format_instructions}
"""

human_template = """
Analysis objective:
{objective}

Available Tables and descriptions:
{tables}
"""

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["objective", "tables"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
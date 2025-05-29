from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class ObjectiveSummary(BaseModel):
    summerized_objective: str = Field(..., description="Core analysis objective")
    required_data: str = Field(..., description="Data or information needed for the analysis")

parser = PydanticOutputParser(pydantic_object=ObjectiveSummary)


# 프롬프트 템플릿
system_template = """
You will be given texts that is part of a business data analysis plan.

Please summarize:
- The core objective of the analysis
- What data (or tables) are likely needed to achieve it

Output the summary in JSON format in the following structure:
{format_instructions}
"""

human_template = """Text:
{analysis_text}
"""

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["analysis_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
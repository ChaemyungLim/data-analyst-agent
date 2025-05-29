from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class Usecase(BaseModel):
    analysis_topic: str = Field(..., alias="Analysis Topic")
    suggested_methodology: str = Field(..., alias="Suggested Methodology")
    expected_insights: str = Field(..., alias="Expected Insights")

class RecommendedUsecases(BaseModel):
    usecases: list[Usecase] = Field(..., alias="Usecases")
    class Config:
        populate_by_name = True  # alias로도 값을 받을 수 있게 허용

parser = PydanticOutputParser(pydantic_object=RecommendedUsecases)

system_template = """
You are a business data analyst.

Your job is to generate up to 3 specific, concrete analysis Usecases based on:
- A table description
- Related tables information

For each idea, include:
- Analysis Topic: (what specific relationship or pattern you propose to study)
- Suggested Methodology: (what kind of statistical analysis, aggregation, segmentation, or modeling would be appropriate)
- Expected Insights: (what kind of business value or decision-making this analysis could support)

Respond in a numbered list. Avoid vague suggestions.
{format_instructions}
"""

human_template = """
[Table Description]
{table_description}

[Related Tables]
{related_tables}
"""

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["table_description", "related_tables"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

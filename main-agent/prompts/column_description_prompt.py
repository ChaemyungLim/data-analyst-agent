from typing import List, Union
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class ColumnDescription(BaseModel):
    column_name: str
    data_type: str
    nullable: str  # YES or NO
    nulls: Union[int, str]  # 대부분 int인데 가끔 unknown이 있을 수도 있음
    notes: List[str]

class TableAnalysis(BaseModel):
    table_description: str
    columns: List[ColumnDescription]
    analysis_considerations: str

parser = PydanticOutputParser(pydantic_object=TableAnalysis)

system_template = """You are a professional data analyst specialized in database documentation and exploratory data analysis (EDA).

You will be given a table name and a summary of its columns.
Your task is to provide a structured analysis consisting of the following sections:

1. Table Description  
   - Briefly describe what kind of data is stored and its business purpose.

2. Column Descriptions and Analytical Notes
   - For each column, describe the following attributes in JSON format:
     - column_name
     - data_type
     - nullable ("YES" or "NO")
     - nulls (number of NULL values; if unknown, set to -1)
     - notes (useful analytical observations that should be considered for data analysis)

Notes must:
- Provide meaningful insights from a data analysis perspective (e.g., likelihood of being an identifier, presence of outliers, skewed distributions, repeated values, narrow/wide range issues).
- Be practical advice for downstream analysis, not superficial descriptions.
- If multiple notes exist, number them clearly as "1.", "2.", "3.", etc.
- There is no limit to the number of notes — include as many analytical observations as are relevant. If there are no notes, return empty notes list.

Each column must be formatted as a JSON object like this:

{{
  "column_name": "string",
  "data_type": "string",
  "nullable": "YES" or "NO",
  "nulls": integer,
  "notes": [
    "1. note1",
    "2. note2,
    "3. note3"
  ]
}}

3. Analysis Considerations
   - Summarize any overall risks, opportunities, or important observations when working with this table.

Finally, format your entire output strictly following the full JSON schema:
{format_instructions}
"""

human_template = """
[Table Name]: {table_name}

[Column Summary Information]:
{column_summary}
"""

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["table_name", "column_summary"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
from typing import TypedDict, Annotated

class TableState(TypedDict):
    input: str
    table_analysis: Annotated[dict, None]
    related_tables: Annotated[dict, None]
    recommended_analysis: Annotated[str, None]
    final_output: Annotated[str, None]
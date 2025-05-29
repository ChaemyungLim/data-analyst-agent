from utils.llm import call_llm
from prompts.recommend_usecases_prompt import prompt, parser

def recommend_analysis(table_description: str, related_tables_info: dict) -> str:
    recommendation = call_llm(
        prompt=prompt,
        parser=parser,
        variables={
            "table_description": table_description,
            "related_tables": related_tables_info
        }
    )
    return recommendation

def recommend_analysis_node(state):
    full_description = state["table_analysis"]
    related_tables_info = state["related_tables"]

    columns_info = full_description.get("columns", [])
    table_description = full_description.get("table_description", "")

    recommendation = recommend_analysis(table_description, related_tables_info)

    final_output = {
        "table_name": state.get("input", ""),
        "table_analysis": {
            "table_description": table_description.strip(),
            "columns": [
                {
                    "column_name": col["column_name"],
                    "data_type": col["data_type"],
                    "nullable": col["nullable"],
                    "nulls": col["nulls"],
                    "notes": col.get("notes", [])
                }
                for col in columns_info
            ],
            "analysis_considerations": full_description.get("analysis_considerations", "")
        },
        "related_tables": {
            table: reason for table, reason in related_tables_info.items()
        },
        "recommended_analysis": [
            {
                "Analysis_Topic": uc.analysis_topic,
                "Suggested_Methodology": uc.suggested_methodology,
                "Expected_Insights": uc.expected_insights
            }
            for uc in recommendation.usecases
        ]
    }

    return {
        "recommended_analysis": recommendation,
        "final_output": final_output
    }
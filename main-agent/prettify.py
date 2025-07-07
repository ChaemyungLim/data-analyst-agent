import re

def print_final_output_task3(final_output: dict) -> str:
    lines = []

    # 1. Objective Summary
    lines.append("📌 [1] Objective Summary")
    lines.append(final_output.get("objective_summary", "No summary found. Something went wrong!"))
    lines.append("")

    # # 2. Recommended Tables
    # lines.append("📌 [2] Recommended Tables")
    # tables = final_output.get("recommended_tables", [])
    # if tables:
    #     for i, table in enumerate(tables, 1):
    #         lines.append(f"{i}. `{table}`")
    # else:
    #     lines.append("No tables recommended.")
    # lines.append("")

    # 2. Recommended Tables (Important Columns 추가)
    lines.append("📌 [2] Recommended Tables")
    tables = final_output.get("recommended_tables", [])
    if tables:
        for i, t in enumerate(tables, 1):
            table_name = t.table  # Pydantic 모델 속성 접근
            cols = t.important_columns
            col_text = ", ".join(cols)
            lines.append(f"{i}. '{table_name}' — {col_text}")
    else:
        lines.append("No tables recommended.")
    lines.append("")

    # 3. Recommended Analysis Method
    lines.append("📌 [3] Recommended Analysis Method")
    method_text = final_output.get("recommended_method", "No method recommended. Something went wrong!")
    method_text = re.sub(r'(?<!^)(?<!\n)(\d+\.\s)', r'\n\1', method_text)
    lines.append(method_text)
    # lines.append(final_output.get("recommended_method", "No method recommended. Something went wrong!"))
    lines.append("")

    # 4. ERD Image Path
    lines.append("📌 [4] ERD Image Path")
    lines.append(final_output.get("erd_image_path", "No ERD path. Something went wrong!"))

    return "\n".join(lines)


def print_final_output_task2(final_output: dict) -> str:
    lines = []

    # 1. Table Name
    lines.append(f"📌 [1] Table Name\n`{final_output.get('table_name', '')}`\n")

    # 2. Table Description
    table_analysis = final_output.get("table_analysis", {})
    lines.append("📌 [2] Table Description")
    lines.append(table_analysis.get("table_description", "[No description]") + "\n")

    # 3. Column Descriptions
    columns = table_analysis.get("columns", [])
    lines.append("📌 [3] Column Descriptions")
    if columns:
        for col in columns:
            col_line = f"- {col['column_name']} ({col['data_type']}, nullable: {col['nullable']}, nulls: {col['nulls']})"
            notes = col.get("notes", [])
            if isinstance(notes, str):
                col_line += f"\n  - {notes}"
            elif isinstance(notes, list):
                for note in notes:
                    col_line += f"\n  - {note}"
            lines.append(col_line)
    else:
        lines.append("- [No column information]")
    lines.append("")

    # 4. Analysis Considerations
    lines.append("📌 [4] Analysis Considerations")
    lines.append(table_analysis.get("analysis_considerations", "[No considerations]") + "\n")

    # 5. Related Tables
    related_tables = final_output.get("related_tables", {})
    lines.append("📌 [5] Related Tables & Reasons")
    if related_tables:
        for table, reason in related_tables.items():
            lines.append(f"- `{table}`: {reason}")
    else:
        lines.append("- [No related tables found]")
    lines.append("")

    # 6. Recommended Analyses
    recommended = final_output.get("recommended_analysis", [])
    lines.append("📌 [6] Recommended Analysis")
    if recommended:
        for i, analysis in enumerate(recommended, 1):
            lines.append(f"{i}. {analysis['Analysis_Topic']}")
            lines.append(f"  - Methodology: {analysis['Suggested_Methodology']}")
            lines.append(f"  - Expected Insights: {analysis['Expected_Insights']}")
    else:
        lines.append("- [No recommended analyses]")
    
    return "\n".join(lines)

def print_final_output_task1(final_output: dict) -> str:
    lines = []

    # 1. SQL
    lines.append("📌 [1] Generated SQL Code")
    lines.append(str(final_output.get("sql", "No SQL generated. Something went wrong!")))
    lines.append("")

    # 2. Result
    # lines.append("📌 [2] SQL Execution Result")
    # lines.append(str(final_output.get("result", "No result found. Something went wrong!")))
    # lines.append("")

    # 2. Result
    lines.append("📌 [2] SQL Execution Result")

    result = final_output.get("result")
    columns = final_output.get("columns")

    if isinstance(result, list):
        display_rows = result[:5] if len(result) > 5 else result
        
        if columns:
            col_widths = [len(col) for col in columns]
            for row in display_rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

            row_format = " | ".join(f"{{:<{w}}}" for w in col_widths)
            # 헤더 출력
            lines.append(row_format.format(*columns))
            lines.append("-" * (sum(col_widths) + 3 * (len(columns) - 1)))
            # 행 출력
            for row in display_rows:
                lines.append(row_format.format(*[str(cell) for cell in row]))
        else:
            # 열 정보 없을 경우 그냥 출력
            for row in display_rows:
                lines.append(" | ".join(str(cell) for cell in row))
        if len(result) > 5:
            lines.append(f"\nToo many rows returned ({len(result)} rows). Showing top 5.")
    else:
        lines.append(str(result))
    lines.append("")
    
    # 3. Error
    lines.append("📌 [3] Error")
    if final_output.get("error"):
        lines.append(str(final_output.get("error")))
        lines.append("")
    else:
        lines.append("No error found. SQL executed successfully!")
        lines.append("")

    # 4. Review
    if final_output.get("llm_review"):
        lines.append("📌 [4] LLM Review on Output")
        review = final_output["llm_review"]
        if isinstance(review, list):
            lines.extend(str(r) for r in review)  # 리스트면 요소들 하나하나 붙이기
        else:
            lines.append(str(review))
        lines.append("")

    return "\n".join(lines)
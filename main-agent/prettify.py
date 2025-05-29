def print_final_output_task3(final_output: dict) -> str:
    lines = []

    # 1. Objective Summary
    lines.append("📌 [1] Objective Summary")
    lines.append(final_output.get("objective_summary", "No summary found. Something went wrong!"))
    lines.append("")

    # 2. Recommended Tables
    lines.append("📌 [2] Recommended Tables")
    tables = final_output.get("recommended_tables", [])
    if tables:
        for i, table in enumerate(tables, 1):
            lines.append(f"{i}. `{table}`")
    else:
        lines.append("No tables recommended.")
    lines.append("")

    # 3. Recommended Analysis Method
    lines.append("📌 [3] Recommended Analysis Method")
    lines.append(final_output.get("recommended_method", "No method recommended. Something went wrong!"))
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
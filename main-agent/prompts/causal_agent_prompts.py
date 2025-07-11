from typing import List
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

### 1. Causal Question Parsing Prompt
class ParsedCausalQuery(BaseModel):
    treatment: str = Field(..., description="Name of treatment variable (even if derived)")
    treatment_expression: str = Field(..., description="SQL expression to compute the treatment (can be CASE WHEN, etc.)")
    treatment_expression_description: str = Field(..., description="Human-readable description of what the treatment expression represents")
    
    outcome: str = Field(..., description="Name of outcome variable (even if derived)")
    outcome_expression: str = Field(..., description="SQL expression to compute the outcome")
    outcome_expression_description: str = Field(..., description="Human-readable description of what the outcome expression represents")

    main_table: str = Field(..., description="Primary table to use")
    join_tables: List[str] = Field(..., description="Additional related tables to join")
    confounders: List[str] = Field(..., description="List of confounders in 'table.column' or SQL expression format")
    mediators: List[str] = Field(default_factory=list, description="List of mediators in 'table.column' or SQL expression format (optional)")
    instrumental_variables: List[str] = Field(default_factory=list, description="List of instrumental variables in 'table.column' or SQL expression format (optional)")
    
parse_query_parser = PydanticOutputParser(pydantic_object=ParsedCausalQuery)

parse_query_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an expert causal data analyst.

Given a natural language question and a set of database table descriptions, extract the following fields:

- treatment: the variable being manipulated
- outcome: the variable being affected
- treatment_expression / outcome_expression: SQL expressions to compute the variables (may use CASE WHEN, COUNT, etc.)
- treatment_expression_description / outcome_expression_description: natural language explanations of what the expressions represent
- main_table: the primary table containing the data
- join_tables: any additional tables that should be joined
- confounders: variables to adjust for in the analysis
- mediators: variables that mediate the causal effect (optional)
- instrumental_variables: variables for IV estimation (optional)

## Rules:
- Only use column names and relationships from the provided table schemas.
- Do not include table aliases like "cu" or "r". Use full table names only
- If the treatment or outcome refers to whether an event occurred (e.g., “used a coupon”, “wrote a review”) or the likelihood of an action, define a binary variable using `CASE WHEN ... THEN 1 ELSE 0 END`.
- If it refers to the number of events (e.g., “number of reviews”), use `COUNT(...)`.
- If it refers to a continuous value (e.g., a rating score), use the raw column name.
- Avoid identifier-like columns (e.g., user_id, product_id, review_id) as confounders or treatment/outcome variables.
- You must fill out both the expression and its explanation for both treatment and outcome.

Do not include any explanations outside the schema. Only return the parsed values in the required format.

{format_instructions}
"""),
    ("human", """
Question:
{question}

Table Descriptions:
{tables}
""")
]).partial(format_instructions=parse_query_parser.get_format_instructions())

### 2. SQL Generation Prompt
class GeneratedSQL(BaseModel):
    sql_query: str = Field(..., description="A valid SQL query to fetch data for causal analysis")

sql_query_parser = PydanticOutputParser(pydantic_object=GeneratedSQL)

sql_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior data analyst tasked with generating SQL for causal inference.

Given:
- treatment: the variable that was manipulated
- outcome: the variable that was affected
- treatment_expression / outcome_expression: SQL expressions representing the variables
- treatment_expression_description / outcome_expression_description: what these expressions represent
- main_table: the main data table
- join_tables: other tables to join with
- confounders: variables to control for
- mediators: optional mediating variables
- instrumental_variables: optional IV variables

Use the provided table schemas to write a SQL query that:
- selects:
  - the treatment expression as `{treatment}` using `AS`
  - the outcome expression as `{outcome}` using `AS`
  - all confounders, mediators, and instrumental variables
- joins tables correctly (using foreign key relationships)
- returns a flat, analysis-ready table

### Rules:
- Use only the tables and columns from the schema
- Do not repeat treatment or outcome in the confounders list
- Do not include any explanatory text — only output the SQL query

{format_instructions}
"""),
    ("human", """
Treatment: {treatment}
Treatment Expression: {treatment_expression}
Treatment Expression Description: {treatment_expression_description}
Outcome: {outcome}
Outcome Expression: {outcome_expression}
Outcome Expression Description: {outcome_expression_description}
Main Table: {main_table}
Join Tables: {join_tables}
Confounders: {confounders}
Mediators: {mediators}
Instrumental Variables: {instrumental_variables}

Table Descriptions:
{table_schemas}
""")
]).partial(format_instructions=sql_query_parser.get_format_instructions())


### 3. SQL Fix Prompt (on failure)

class FixedSQL(BaseModel):
    sql_query: str = Field(..., description="A revised valid SQL query that resolves the original error")

fix_sql_parser = PydanticOutputParser(pydantic_object=FixedSQL)

fix_sql_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior data analyst. Your task is to revise a faulty SQL query based on the error message returned during execution.

You will be given:
1. The original SQL query
2. The error message it triggered
3. The intended treatment/outcome variable names and SQL expressions
4. A list of confounders, mediators, and instrumental variables
5. The main and joined tables
6. Table schema descriptions

Your job is to modify the SQL query to resolve the error while preserving the original intent. Be sure to:
- Correct incorrect column names or aliases
- Fix joins if necessary
- Use the correct treatment and outcome expressions with aliases
- Ensure all required variables (treatment, outcome, confounders, etc.) are selected
- Join the right tables using valid keys
- Use only columns and tables from the provided schemas

Return only the fixed SQL query. Do not include explanations or comments.

{format_instructions}
"""),
    ("human", """
Original SQL Query:
```sql
{original_sql}
```

Error Message:
```
{error_message}
```
Treatment: {treatment}
Treatment Expression: {treatment_expression}
Treatment Expression Description: {treatment_expression_description}

Outcome: {outcome}
Outcome Expression: {outcome_expression}
Outcome Expression Description: {outcome_expression_description}

Main Table: {main_table}
Join Tables: {join_tables}
Confounders: {confounders}
Mediators: {mediators}
Instrumental Variables: {instrumental_variables}

Table Schemas:
{table_schemas}
""")
]).partial(format_instructions=fix_sql_parser.get_format_instructions())

## 4. Causal Strategy Selection Prompt
class SelectedCausalStrategy(BaseModel):
    causal_task: str = Field(..., description="Overall causal task (e.g., estimating_causal_effect, mediation_analysis, causal_prediction, what_if)")
    identification_strategy: str = Field(..., description="Strategy used to identify the causal effect, e.g., backdoor, frontdoor, iv, mediation")
    estimation_method: str = Field(..., description="Estimation method compatible with identification strategy")
    refutation_methods: List[str] = Field(..., description="Optional refutation methods to test robustness")

strategy_output_parser = PydanticOutputParser(pydantic_object=SelectedCausalStrategy)

causal_strategy_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a causal inference expert using the DoWhy library.

Your job is to choose the appropriate causal inference strategy, estimation method, and optional refutation methods given:
- A user's causal question
- Extracted variables (treatment, outcome, confounders)
- Basic data preview

Only choose from the valid options defined below.

---
Causal Tasks:
- estimating_causal_effect: estimate average treatment effect (ATE)
- mediation_analysis: decompose effect via mediators
- causal_prediction: predict outcome using causal structure (e.g., TabPFN)
- what_if: simulate counterfactuals
- root_cause: identify potential causes of outcome

Identification Strategies:
- backdoor: adjust for confounders that affect both treatment and outcome
- frontdoor: identify effect using mediators when backdoor not available
- iv: use instrumental variables for exogenous variation
- mediation: isolate indirect vs direct effects
- id_algorithm: automated graphical ID algorithm

Estimation Methods:
- backdoor.linear_regression: basic OLS on adjusted data
- backdoor.propensity_score_matching: match units by treatment probability
- backdoor.propensity_score_stratification: stratify by score and estimate
- backdoor.propensity_score_weighting: reweight sample by inverse propensity
- backdoor.distance_matching: match using nearest-neighbor distance
- backdoor.generalized_linear_model: GLM for non-normal outcomes
- iv.instrumental_variable: two-stage least squares using IV
- iv.regression_discontinuity: exploit cutoff-based variation
- frontdoor.two_stage_regression: mediator-based 2-stage estimator
- mediation.two_stage_regression: mediation-specific 2-stage model
- causal_prediction.tabpfn: use TabPFN to predict causal outcomes
- what_if.simple_model: simulate counterfactual with regression
- what_if.tabpfn: simulate counterfactual using TabPFN

Refutation Methods (optional):
- placebo_treatment_refuter: randomly replace treatment and re-test
- random_common_cause: add synthetic common cause to check stability
- data_subset_refuter: re-run analysis on subsets
- add_unobserved_common_cause: simulate bias from unobserved variables

{format_instructions}
"""),
    ("human", """
User Causal Question:
{question}

Parsed Variables:
- Treatment: {treatment}
- Outcome: {outcome}
- Confounders: {confounders}

Data Sample:
{df_sample}
""")
]).partial(format_instructions=strategy_output_parser.get_format_instructions())

## 5. Causal Analysis Result Generation Prompt
class CausalResultExplanation(BaseModel):
    explanation: str = Field(..., description="Plain-text summary of the causal analysis results.")

generate_answer_parser = PydanticOutputParser(pydantic_object=CausalResultExplanation)

generate_answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a causal inference expert. Based on the following information, write a short but informative explanation of the causal analysis results. Your explanation should be accessible to data-literate users.

- Type of causal task: {task}
- Estimation method used: {estimator}
- Estimated causal effect value: {effect_value}
- Refutation result (if any): {refutation_result}
- Label mappings (optional): {label_maps},  Use these to translate coded values (e.g., 0/1) into human-readable labels.

Your explanation should include:
1. Interpretation of the estimated effect,
2. Whether the effect seems statistically or practically significant,
3. Whether the refutation result supports or weakens confidence in the effect,
4. Any caveats or assumptions that should be kept in mind.
5. If label mappings are provided, interpret the effect using human-readable category names

Use a clear, neutral tone and aim for a short analytical summary (3–6 sentences).

{format_instructions}
"""),
    ("human", "")
]).partial(format_instructions=generate_answer_parser.get_format_instructions())
import json
from tqdm import tqdm

from agents.causal_analysis.state import DEFAULT_EXPRESSION_DICT
from agents.causal_analysis.graph import generate_causal_analysis_graph
from utils.llm import get_llm
from utils.load_causal_graph import load_causal_graph

import os

# LLM, Graph 불러오기
llm = get_llm(model="gpt-4o-mini", temperature=0.7, provider="openai")
causal_graph = load_causal_graph("experiments/causal_analysis/causal_graph_full.json")
app = generate_causal_analysis_graph(llm=llm)

# 경로 설정
input_path = "experiments/causal_analysis/causal_queries_w_answers.json"
result_path = "experiments/results/causal_eval_results.jsonl"
summary_path = "experiments/results/causal_eval_summary.json"

# 디렉토리 생성
os.makedirs(os.path.dirname(result_path), exist_ok=True)

# 변수 초기화
total, success_count, within_ci_count = 0, 0, 0

# 결과 파일 초기화
open(result_path, "w").close()

# 질문 불러오기
with open(input_path, "r") as f:
    queries = json.load(f)

for q in tqdm(queries, desc="Evaluating causal questions"):
    total += 1
    question = q["question"]
    try:
        treatment = q["treatment"]
        outcome = q["outcome"]
        confounders = q.get("confounders", [])
        mediators = q.get("mediators", [])
        instrumental_variables = q.get("instrumental_variables", [])

        treatment_expr = DEFAULT_EXPRESSION_DICT.get(treatment, treatment)
        outcome_expr = DEFAULT_EXPRESSION_DICT.get(outcome, outcome)
        confounder_exprs = [DEFAULT_EXPRESSION_DICT.get(c, c) for c in confounders]

        state_input = {
            "input": question,
            "db_id": "daa",
            "variable_info": {
                "treatment": treatment,
                "treatment_expression": treatment_expr,
                "outcome": outcome,
                "outcome_expression": outcome_expr,
                "confounders": confounders,
                "confounder_expressions": confounder_exprs,
                "mediators": mediators,
                "instrumental_variables": instrumental_variables
            },
            "causal_graph": causal_graph,
            "expression_dict": DEFAULT_EXPRESSION_DICT
        }

        result = app.invoke(state_input)

        estimated_ate = result.get("causal_effect_value") or result.get("causal_effect_ate")
        ci = result.get("confidence_interval")
        p_value = result.get("causal_effect_p_value")

        ground_truth_ate = q.get("ground_truth_ate")
        ground_truth_ci = q.get("confidence_interval")
        if isinstance(ground_truth_ci[0], list):  # nested list case
            ground_truth_ci = ground_truth_ci[0]

        within_gt_ci = (
            ground_truth_ci[0] <= estimated_ate <= ground_truth_ci[1]
            if estimated_ate is not None else None
        )
        
        success_count += 1
        if within_gt_ci:
            within_ci_count += 1

        result_dict = {
            "question": question,
            "success": True,
            "estimated_ate": estimated_ate,
            "ground_truth_ate": ground_truth_ate,
            "absolute_error": abs(estimated_ate - ground_truth_ate) if estimated_ate is not None else None,
            "within_ground_truth_ci": within_gt_ci,
            "p_value": p_value,
            "estimation_method": result.get("estimation_method"),
            "ground_truth_method": q.get("estimation_method")
        }

    except Exception as e:
        result_dict = {
            "question": question,
            "success": False,
            "error_message": str(e)
        }
        
    # JSONL 방식으로 저장
    with open(result_path, "a") as f:
        f.write(json.dumps(result_dict) + "\n")


# 요약 정보 저장
summary = {
    "total": total,
    "success_count": success_count,
    "ci_coverage_count": within_ci_count,
    "success_rate": round(within_ci_count / success_count * 100, 2) if success_count > 0 else 0.0,
}  

with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)

print("\n✅ Evaluation complete.")
print(f"Results saved to: {result_path}")
print(f"Summary saved to: {summary_path}")
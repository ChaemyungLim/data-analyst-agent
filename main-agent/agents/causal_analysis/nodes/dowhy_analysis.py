# nodes/dowhy_analysis.py

from typing import Dict, List
from langchain_core.runnables import RunnableLambda

import pandas as pd
from dowhy import CausalModel
from tabpfn import TabPFNClassifier

import statsmodels.api as sm

def clean_var_names(vars: List[str]) -> List[str]:
    return [v.split(".")[-1] if isinstance(v, str) and "." in v else v for v in vars]

def build_dowhy_analysis_node() -> RunnableLambda:
    """
    Performs causal analysis using the selected strategy and preprocessed data.
    """

    def invoke(state: Dict) -> Dict:
        strategy = state["strategy"]
        parsed_info = state["parsed_query"]
        df: pd.DataFrame = state["df_preprocessed"]
        
        if df is None or df.shape[0] < 10:
            raise ValueError(f"Insufficient data for analysis: {df.shape[0]} rows found, at least 10 required.")

        if not strategy or not parsed_info:
            raise ValueError("Missing strategy or parsed query.")

        # Extract variables
        treatment = clean_var_names([parsed_info.get("treatment")])[0]
        outcome = clean_var_names([parsed_info.get("outcome")])[0]
        confounders = clean_var_names(parsed_info.get("confounders", []))
        mediators = clean_var_names(parsed_info.get("mediators", []))
        ivs = clean_var_names(parsed_info.get("instrumental_variables", []))


        # Step 1: Create CausalModel
        causal_graph = state.get("causal_graph", {})
        dot_graph = causal_graph.get("dot_graph")
        
        try:
            if dot_graph:
                model = CausalModel(
                    data=df,
                    treatment=treatment,
                    outcome=outcome,
                    common_causes=confounders if strategy.identification_method == "backdoor" else None,
                    instruments=ivs if strategy.identification_method == "iv" else None,
                    mediators=mediators if strategy.identification_method == "mediation" else None,
                    graph=dot_graph
                )
            else:
                model = CausalModel(
                    data=df,
                    treatment=treatment,
                    outcome=outcome,
                    common_causes=confounders if strategy.identification_method == "backdoor" else None,
                    instruments=ivs if strategy.identification_method == "iv" else None,
                    mediators=mediators if strategy.identification_method == "mediation" else None,
                )
        except Exception as e:
            raise RuntimeError(f"Failed to construct CausalModel: {e}")
        
        identified_estimand = model.identify_effect()
        
        method_params = {}

        # Step 2: Handle GLM family
        if strategy.estimator == "backdoor.generalized_linear_model":
            unique_vals = df[outcome].dropna().unique()
            if len(unique_vals) == 2 and set(unique_vals).issubset({0, 1, True, False, 1, 2}):
                method_params["glm_family"] = sm.families.Binomial()
            else:
                method_params["glm_family"] = sm.families.Gaussian()

        # Step 3: TabPFN-based propensity score modeling
        classification_estimators = [
            "backdoor.propensity_score_matching",
            "backdoor.propensity_score_stratification",
            "backdoor.propensity_score_weighting",
            "backdoor.distance_matching"
        ]
        if strategy.estimator in classification_estimators:
            method_params["propensity_score_model"] = TabPFNClassifier()

            # Encode categorical columns
            cat_cols = df.select_dtypes(include="category").columns
            if len(cat_cols) > 0:
                label_maps = {}
                for col in cat_cols:
                    df[col], uniques = df[col].factorize()
                    label_maps[col] = dict(enumerate(uniques))
                state["label_maps"] = label_maps
        
        # Step 4: Estimate causal effect
        try:
            estimate = model.estimate_effect(
                identified_estimand,
                method_name=strategy.estimator,
                method_params=method_params if method_params else None
            )
        except Exception as e:
            raise RuntimeError(f"Failed to estimate causal effect: {e}")

        # Step 5: Optional refutation
        if strategy.refuter:
            refute_result = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name=strategy.refuter[0],
            )
            state["refutation_result"] = refute_result.summary()

        # Step 6: Save to state
        state["causal_model"] = model
        state["causal_estimand"] = identified_estimand
        state["causal_estimate"] = estimate
        
        # Save useful scalar values separately
        try:
            ci = estimate.conf_int()
        except Exception:
            ci = None

        state["causal_effect_value"] = float(getattr(estimate, "effect", None)) if getattr(estimate, "effect", None) is not None else None
        state["causal_effect_ci"] = ci
        state["causal_effect_ate"] = float(getattr(estimate, "value", None)) if getattr(estimate, "value", None) is not None else None
        state["causal_effect_p_value"] = float(getattr(estimate, "p_value", None)) if getattr(estimate, "p_value", None) is not None else None
        state["estimation_method"] = strategy.estimator

        return state

    return RunnableLambda(invoke)
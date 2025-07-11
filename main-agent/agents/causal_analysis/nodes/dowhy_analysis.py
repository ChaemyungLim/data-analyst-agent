# nodes/dowhy_analysis.py

from typing import Dict
from langchain_core.runnables import RunnableLambda

import pandas as pd
from dowhy import CausalModel
from tabpfn import TabPFNClassifier


def build_dowhy_analysis_node() -> RunnableLambda:
    """
    Performs causal analysis using the selected strategy and preprocessed data.
    """

    def invoke(state: Dict) -> Dict:
        strategy = state["strategy"]
        parsed_info = state["parsed_query"]
        df: pd.DataFrame = state["df_preprocessed"]

        if not strategy or not parsed_info or df is None:
            raise ValueError("Missing strategy, parsed_info, or df_preprocessed")

        treatment = parsed_info.get("treatment")
        treatment = treatment.split(".")[-1] if treatment else None

        outcome = parsed_info.get("outcome")
        outcome = outcome.split(".")[-1] if outcome else None

        confounders = [c.split(".")[-1] for c in parsed_info.get("confounders", [])]
        mediators = [m.split(".")[-1] for m in parsed_info.get("mediators", [])]
        ivs = [i.split(".")[-1] for i in parsed_info.get("instrumental_variables", [])]

        # Step 1: Define CausalModel
        model = CausalModel(
            data=df,
            treatment=treatment,
            outcome=outcome,
            common_causes=confounders if strategy.identification_strategy == "backdoor" else None,
            instruments=ivs if strategy.identification_strategy == "iv" else None,
            mediators=mediators if strategy.identification_strategy == "mediation" else None,
        )

        identified_estimand = model.identify_effect()

        # Step 2: TabPFN 모델 적용 가능한 경우는 TabPFN을 사용하여 추정
        method_params = {}
        classification_estimators = [
            "backdoor.propensity_score_matching",
            "backdoor.propensity_score_stratification",
            "backdoor.propensity_score_weighting",
            "backdoor.distance_matching"
        ]

        if strategy.estimation_method in classification_estimators:
            method_params["propensity_score_model"] = TabPFNClassifier()

            # Handle categorical variables: convert to numeric codes and store mappings
            label_maps = {}
            # Only convert if there are categorical columns
            cat_cols = df.select_dtypes(include="category").columns
            if len(cat_cols) > 0:
                for col in cat_cols:
                    df[col], uniques = df[col].factorize()
                    label_maps[col] = dict(enumerate(uniques))
                state["label_maps"] = label_maps

        estimate = model.estimate_effect(
            identified_estimand,
            method_name=strategy.estimation_method,
            method_params=method_params if method_params else None
        )

        # Step 3: Optional refutation
        if strategy.refutation_methods:
            refute_result = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name=strategy.refutation_methods[0],
            )
            state["refutation_result"] = refute_result.summary()

        # Step 4: Save results to state
        state["causal_model"] = model
        state["causal_estimand"] = identified_estimand
        state["causal_estimate"] = estimate

        return state

    return RunnableLambda(invoke)
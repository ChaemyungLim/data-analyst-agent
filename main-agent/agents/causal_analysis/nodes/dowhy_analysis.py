# nodes/dowhy_analysis.py

from typing import Dict
from langchain_core.runnables import RunnableLambda

import pandas as pd
from dowhy import CausalModel
from tabpfn import TabPFNClassifier, TabPFNRegressor



def build_dowhy_analysis_node() -> RunnableLambda:
    """
    Performs causal analysis using the selected strategy and preprocessed data.
    """

    def invoke(state: Dict) -> Dict:
        strategy = state.get("strategy")
        parsed_info = state.get("parsed_query")
        df: pd.DataFrame = state.get("df_preprocessed")

        if not strategy or not parsed_info or df is None:
            raise ValueError("Missing strategy, parsed_info, or df_preprocessed")

        treatment = parsed_info.get("treatment")
        outcome = parsed_info.get("outcome")
        confounders = parsed_info.get("confounders", [])
        mediators = parsed_info.get("mediators", [])
        ivs = parsed_info.get("instrumental_variables", [])

        # Step 1: Define CausalModel
        model = CausalModel(
            data=df,
            treatment=treatment,
            outcome=outcome,
            common_causes=confounders if strategy.identification_method == "backdoor" else None,
            instruments=ivs if strategy.identification_method == "iv" else None,
            mediators=mediators if strategy.identification_method == "mediation" else None,
        )

        identified_estimand = model.identify_effect()

        # Step 2: TabPFN 모델 자동 지정
        method_params = {}
        classification_estimators = [
            "backdoor.propensity_score_matching",
            "backdoor.propensity_score_stratification",
            "backdoor.propensity_score_weighting",
        ]
        regression_estimators = [
            "backdoor.linear_regression",
            "backdoor.generalized_linear_model",
            "iv.instrumental_variable",
            "mediation.mediate_effect",
        ]

        if strategy.estimator in classification_estimators:
            method_params["propensity_score_model"] = TabPFNClassifier()
        elif strategy.estimator in regression_estimators:
            method_params["regression_model"] = TabPFNRegressor()

        estimate = model.estimate_effect(
            identified_estimand,
            method_name=strategy.estimator,
            method_params=method_params if method_params else None
        )

        # Step 3: Optional refutation
        if strategy.refuter:
            refute_result = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name=strategy.refuter,
            )
            state["refutation_result"] = refute_result.summary()

        # Step 4: Save results to state
        state["causal_model"] = model
        state["causal_estimand"] = identified_estimand
        state["causal_estimate"] = estimate

        return state

    return RunnableLambda(invoke)
# causal_analysis/nodes/preprocess.py

import pandas as pd
from typing import Dict
from sklearn.preprocessing import StandardScaler

def build_preprocess_node(state: Dict) -> Dict:
    df: pd.DataFrame = state.get("df")
    parsed_info = state.get("parsed_info")

    if df is None or parsed_info is None:
        raise ValueError("Missing required inputs: 'df' or 'parsed_info'.")

    treatment = parsed_info.get("treatment")
    outcome = parsed_info.get("outcome")
    confounders = parsed_info.get("confounders", [])
    mediators = parsed_info.get("mediators", [])
    ivs = parsed_info.get("instrumental_variables", [])

    all_vars = [treatment, outcome] + confounders + mediators + ivs
    all_vars = list(dict.fromkeys(all_vars))  # 중복 제거

    df = df[all_vars]
    df = df.dropna(subset=all_vars)

    if df.empty:
        raise ValueError("All rows removed after dropping nulls.")

    # 범주형 변수 원-핫 인코딩
    df = pd.get_dummies(df, drop_first=True)

    # 수치형 변수 정규화
    scaler = StandardScaler()
    df[df.columns] = scaler.fit_transform(df)

    state["df_preprocessed"] = df
    return state
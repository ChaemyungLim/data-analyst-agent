# causal_analysis/nodes/preprocess.py

import pandas as pd
from typing import Dict
from sklearn.preprocessing import StandardScaler

def build_preprocess_node():
    def node(state: Dict) -> Dict:
        df: pd.DataFrame = state["df_raw"]  # 수정: df_raw에서 시작
        parsed_query = state["parsed_query"]

        if df is None or parsed_query is None:
            raise ValueError("Missing required inputs: 'df_raw' or 'parsed_query'.")

        treatment = parsed_query.get("treatment")
        outcome = parsed_query.get("outcome")
        confounders = parsed_query.get("confounders", [])
        mediators = parsed_query.get("mediators", [])
        ivs = parsed_query.get("instrumental_variables", [])

        all_vars = [treatment, outcome] + confounders + mediators + ivs
        all_vars = list(dict.fromkeys(all_vars))  # 중복 제거
        all_vars = [col.split(".")[-1] for col in all_vars] # 점(.)이 포함된 경우 실제 컬럼명 추출

        # treatment, outcome, confounders, mediators, ivs 컬럼들 중 범주형으로 처리할 것들은 category로 변환
        for col in all_vars:
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].astype("category")

        df = df[all_vars]
        df = df.dropna(subset=all_vars)

        if df.empty:
            raise ValueError("All rows removed after dropping nulls.")

        # 수치형 / 범주형 분리
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()

        # outcome과 treatment는 변환에서 제외
        reserved_cols = [treatment, outcome]
        transform_num_cols = [col for col in num_cols if col not in reserved_cols]

        # 수치형 정규화
        if transform_num_cols:
            scaler = StandardScaler()
            df_num = pd.DataFrame(
                scaler.fit_transform(df[transform_num_cols]),
                columns=transform_num_cols,
                index=df.index,
            )
        else:
            df_num = pd.DataFrame(index=df.index)

        # treatment, outcome, 범주형 변수 포함하여 원본 유지
        df_reserved = df[reserved_cols + cat_cols]

        # 최종 결합
        df_processed = pd.concat([df_reserved, df_num], axis=1)
        state["df_preprocessed"] = df_processed
        return state

    return node
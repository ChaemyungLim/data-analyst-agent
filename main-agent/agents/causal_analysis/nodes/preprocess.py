# causal_analysis/nodes/preprocess.py

import pandas as pd
from typing import Dict
from sklearn.preprocessing import StandardScaler

def build_preprocess_node():
    def node(state: Dict) -> Dict:
        df: pd.DataFrame = state["df_raw"]  # 수정: df_raw에서 시작
        graph_nodes = state["causal_graph"]["nodes"]
        parsed_query = state.get("parsed_query", {})

        if df is None or not graph_nodes:
            raise ValueError("Missing 'df_raw' or 'causal_graph.nodes'.")

        selected_cols = [var.split(".")[-1] for var in graph_nodes]
        df = df[selected_cols].copy()

        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    df[col] = df[col].astype("category")

        df = df.dropna(subset=df.columns)
        if df.empty:
            raise ValueError("All rows removed after dropping nulls.")

        # 정규화 (treatment, outcome 제외)
        treatment = parsed_query.get("treatment")
        outcome = parsed_query.get("outcome")
        reserved_cols = [col for col in [treatment, outcome] if col in df.columns]

        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        transform_cols = [col for col in num_cols if col not in reserved_cols]

        df_num = pd.DataFrame(index=df.index)
        if transform_cols:
            scaler = StandardScaler()
            df_num = pd.DataFrame(
                scaler.fit_transform(df[transform_cols]),
                columns=transform_cols,
                index=df.index
            )

        df_out = pd.concat([df[reserved_cols + cat_cols], df_num], axis=1)
        state["df_preprocessed"] = df_out
        return state

    return node
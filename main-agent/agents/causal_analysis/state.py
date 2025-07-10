# agents/causal_analysis/state.py

from typing import Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
from dowhy import CausalModel
from dowhy.causal_estimator import CausalEstimate


class CausalAnalysisState(BaseModel):
    question: Optional[str] = None  # 사용자 질의
    parsed_query: Optional[Dict[str, Any]] = None  # treatment, outcome, confounders 등
    sql_query: Optional[str] = None  # 생성된 SQL 쿼리
    df_sample: Optional[str] = None  # 데이터 샘플 (string 형태로 LLM에 넣기 위함)
    df_raw: Optional[pd.DataFrame] = None  # 추출된 원본 데이터
    df_preprocessed: Optional[pd.DataFrame] = None  # 전처리된 데이터
    strategy: Optional[Any] = None  # 선택된 전략 (task, estimator 등)
    causal_model: Optional[CausalModel] = None  # dowhy 모델 객체
    causal_estimand: Optional[Any] = None  # identified_estimand
    causal_estimate: Optional[CausalEstimate] = None  # 추정 결과
    refutation_result: Optional[str] = None  # refutation summary (optional)
    final_answer: Optional[str] = None  # 자연어 설명 결과
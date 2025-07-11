# agents/causal_analysis/state.py

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
import pandas as pd
from dowhy import CausalModel
from dowhy.causal_estimator import CausalEstimate

class Strategy(BaseModel):
    task: str
    identification_method: str
    estimator: str
    refuter: Optional[str] = None

class CausalAnalysisState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
        
    input: Optional[str] = None  # 사용자 질의
    db_id: Optional[str] = "daa" # PostgreSQL 연결 ID
    parsed_query: Optional[Dict[str, Any]] = None  # treatment, outcome 등 파싱 결과
    table_schema_str: Optional[str] = None  # Markdown-formatted table schema for SQL generation
    sql_query: Optional[str] = None  # SQL 쿼리
    df_raw: Optional[pd.DataFrame] = None  # 추출된 원본 데이터
    df_preprocessed: Optional[pd.DataFrame] = None  # 전처리된 데이터
    label_maps: Optional[Dict[str, Dict[int, str]]] = None  # 범주형 변수 인코딩 정보 (숫자 → 레이블 매핑)
    strategy: Optional[Strategy] = None  # 선택된 전략 (task, estimator 등)
    
    causal_model: Optional[CausalModel] = None  # dowhy 모델 객체
    causal_estimand: Optional[Any] = None  # identified_estimand
    causal_estimate: Optional[CausalEstimate] = None  # 추정 결과
    refutation_result: Optional[str] = None  # refutation summary (optional)
    final_answer: Optional[str] = None  # 자연어 설명 결과
    
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)
# agents/causal_analysis/state.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
import pandas as pd
from dowhy import CausalModel
from dowhy.causal_estimator import CausalEstimate

DEFAULT_EXPRESSION_DICT = {
    # ─── Users & basic demographics ────────────────────────────────────────────
    "signup_days_ago": "DATE_PART('day', CURRENT_DATE - users.created_at)",
    "is_active":        "users.is_active",
    "age":              "DATE_PART('year', AGE(users.birth))",
    "gender":           "users.gender",
    "point_balance":    "users.point_balance",

    # ─── Order-level amounts & quantities ──────────────────────────────────────
    "unit_price":   "order_items.unit_price",
    "quantity":     "order_items.quantity",
    "order_total":  "order_items.total_price",        # generated column
    "paid_amount":  "(orders.total_amount - orders.discount_amount)",

    # ─── Coupon effects (requires coupon join, see notes) ──────────────────────
    "discount_amount": "coupon.discount_amount",
    "discount_rate":   "coupon.discount_rate",
    "used_coupon":
        "COALESCE((SELECT TRUE "
        "           FROM coupon_usage "
        "           WHERE coupon_usage.order_id = orders.order_id "
        "           LIMIT 1), FALSE)",

    # ─── Loyalty points (1 % of amount actually paid) ─────────────────────────
    "point_earned": "((orders.total_amount - orders.discount_amount) * 0.01)",

    # ─── Reviews ───────────────────────────────────────────────────────────────
    "review_score": "review.score"
}

class Strategy(BaseModel):
    task: str
    identification_method: str
    estimator: str
    refuter: Optional[str] = None

class CausalAnalysisState(BaseModel):
    messages: Optional[List] = []  # 대화 메시지 기록
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

    variable_info: Optional[Dict[str, Any]] = None  # 입력으로 직접 지정된 변수 + 표현식
    expression_dict: Optional[Dict[str, str]] = None  # 전체 변수 → 표현식 매핑
    causal_graph: Optional[Dict[str, Any]] = None  # causal graph의 edges, nodes, graphviz 등
    
    causal_model: Optional[CausalModel] = None  # dowhy 모델 객체
    causal_estimand: Optional[Any] = None  # identified_estimand
    causal_estimate: Optional[CausalEstimate] = None  # 추정 결과
    causal_effect_value: Optional[float] = None  # 추정된 인과 효과 값
    causal_effect_ate: Optional[float] = None  # ATE (Average Treatment Effect)
    causal_effect_p_value: Optional[float] = None  # p-value (optional)
    causal_effect_ci: Optional[Any] = None  # 신뢰 구간 (optional)
    refutation_result: Optional[str] = None  # refutation summary (optional)
    final_answer: Optional[str] = None  # 자연어 설명 결과
    
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)
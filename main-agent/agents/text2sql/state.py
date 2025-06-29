from typing import Optional, List, TypedDict, Annotated

class AgentState(TypedDict):
    messages: List # 대화이력 
    query: str
    desc_str: Optional[str]
    fk_str: Optional[str]
    extracted_schema: Optional[dict]
    final_sql: Optional[str]
    qa_pairs: Optional[str]
    pred: Optional[str]
    result: Optional[List]
    error: Optional[str]
    pruned: bool
    send_to: str
    try_times: int
    llm_review: Optional[str]  # 리뷰 노드에서 사용
    output: Optional[dict]  # system_node 에서 사용
    
    db_id: str # 여러 db 를 쓸 경우
    notes: Optional[str] # 노트는 사용자가 입력한 추가 정보나 힌트
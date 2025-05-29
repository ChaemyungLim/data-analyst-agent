from typing import Dict
import json

from config.redis import redis_client
from utils.llm import call_llm
from prompts.metadata_prompt import prompt, parser


# 테이블 구조 markdown 생성 (LLM 입력용)
def generate_table_markdown(sub_schema: Dict[str, dict]) -> str:
    lines = []
    for table, info in sub_schema.items():
        lines.append(f"### Table: {table}")
        for col, meta in info["columns"].items():
            parts = [f"{col} ({meta['type']})"]

            # 기본 속성
            if meta.get("pk"): parts.append("PK")
            if meta.get("fk"): parts.append(f"FK to {meta['fk']}")
            if meta.get("unique"): parts.append("UNIQUE")
            if meta.get("nullable") is False: parts.append("NOT NULL")
            if meta.get("default") is not None: parts.append(f"DEFAULT {meta['default']}")

            # +) 통계 정보
            if "count" in meta: parts.append(f"count={meta['count']}")
            if "nulls" in meta: parts.append(f"nulls={meta['nulls']}")
            if "distinct" in meta: parts.append(f"distinct={meta['distinct']}")
            if "min" in meta and "max" in meta:
                parts.append(f"range={meta['min']}~{meta['max']}")
            if "avg" in meta: parts.append(f"avg={meta['avg']}")
            if "stddev" in meta: parts.append(f"stddev={meta['stddev']}")
            if "median" in meta: parts.append(f"median={meta['median']}")

            lines.append("- " + ", ".join(parts))

            # +) top_values, examples
            if "top_values" in meta:
                top = ", ".join([f"{k}({v})" for k, v in meta["top_values"].items()])
                parts.append(f"top_values={top}")
            if "examples" in meta:
                examples = ", ".join(meta["examples"])
                parts.append(f"examples=[{examples}]")

        for check in info.get("check_constraints", []):
            lines.append(f"- CHECK: {check}")
        for fk in info.get("foreign_keys", []):
            lines.append(f"- FOREIGN KEY: {fk[0]} → {fk[1]}.{fk[2]}")
        lines.append("")
    return "\n".join(lines)


# 테이블 하나에 대한 메타데이터 생성
def generate_metadata(table_name: str, schema: dict) -> dict:
    schema_md = generate_table_markdown({table_name: schema})
    result = call_llm(prompt=prompt, parser=parser, variables={"schema": schema_md})
    metadata = result.model_dump()
    metadata["schema"] = schema
    return metadata


# Redis에 저장된 기존 데이터와 비교 → 변경된 경우만 업데이트
def update_metadata(table_name: str, schema: dict) -> bool:
    new_metadata = generate_metadata(table_name, schema)
    stored = redis_client.get(f"metadata:{table_name}")
    stored_metadata = json.loads(stored) if stored else {}

    if new_metadata["columns"] != stored_metadata.get("columns"):
        redis_client.set(f"metadata:{table_name}", json.dumps(new_metadata, indent=2))
        redis_client.sadd("metadata:table_names", table_name)
        print(f"Metadata updated for table: {table_name}")
        return True

    print(f"No metadata change for table: {table_name}")
    return False
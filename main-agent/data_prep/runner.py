from .related_tables import extract_schema, update_table_relations
from .metadata import update_metadata

def run():
    print("Starting data prep pipeline...")

    # PostgreSQL에서 스키마 추출
    schema = extract_schema()
    print("- schema extracted...")

    print("--- generating(updating) table relations...")
    # 테이블 관계 자료형 생성 및 업데이트
    schema_changed = update_table_relations()

    # 테이블별 메타데이터 생성 및 업데이트
    print(f"----- generating(updating) metadata..")
    for table_name, table_schema in schema.items():
        update_metadata(table_name, table_schema)

    print("------- Data prep pipeline complete!")

if __name__ == "__main__":
    run()
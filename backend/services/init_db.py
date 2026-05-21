from models.schemas import Base
from services.db_service import engine
from sqlalchemy import inspect, text


def _column_sql(column_name: str, column_type: str):
    return f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}"


def _ensure_task_columns():
    """Add production orchestration columns without requiring Alembic yet.

    The project currently uses create_all directly. This keeps existing local
    databases bootable while documenting the columns that a future Alembic
    migration should own.
    """

    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("tasks")}
    dialect = engine.dialect.name
    text_type = "TEXT"
    string_type = "VARCHAR"
    integer_type = "INTEGER"
    float_type = "DOUBLE PRECISION" if dialect == "postgresql" else "FLOAT"
    timestamp_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"

    required = {
        "state": f"{string_type} DEFAULT 'PENDING'",
        "workflow_id": string_type,
        "retry_count": f"{integer_type} DEFAULT 0",
        "max_retries": f"{integer_type} DEFAULT 2",
        "error_message": text_type,
        "confidence_score": float_type,
        "reasoning_summary": text_type,
        "validation_status": string_type,
        "started_at": timestamp_type,
        "completed_at": timestamp_type,
        "updated_at": timestamp_type,
    }

    with engine.begin() as connection:
        for column_name, column_type in required.items():
            if column_name not in existing:
                connection.execute(text(_column_sql(column_name, column_type)))


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_task_columns()

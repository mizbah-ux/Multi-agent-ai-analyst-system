from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from datetime import datetime
from services.db_service import Base

class User(Base):

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    role = Column(String, default="user")

    refresh_token = Column(String, nullable=True)

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    user_input = Column(Text)
    file_id = Column(String)
    status = Column(String, default="pending")
    state = Column(String, default="PENDING")
    workflow_id = Column(String, nullable=True)
    result_path = Column(String, nullable=True)
    ppt_path = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    error_message = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    validation_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    agent = Column(String)
    message = Column(String)
    status = Column(String)  # running / completed / failed
    timestamp = Column(DateTime, default=datetime.utcnow)


class Workflow(Base):
    __tablename__ = "workflows"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    user_id = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")
    dependency_graph = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentLifecycle(Base):
    __tablename__ = "agent_lifecycle"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True)
    agent_name = Column(String, index=True)
    state = Column(String, index=True)
    confidence_score = Column(Float, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    validation_status = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    event_type = Column(String, index=True)
    task_id = Column(Integer, index=True, nullable=True)
    workflow_id = Column(String, index=True, nullable=True)
    payload = Column(Text, nullable=True)
    status = Column(String, default="published")
    created_at = Column(DateTime, default=datetime.utcnow)


class ToolExecutionRecord(Base):
    __tablename__ = "tool_execution_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True, nullable=True)
    tool_name = Column(String, index=True)
    capability_type = Column(String, index=True)
    status = Column(String, default="completed")
    latency_ms = Column(Float, nullable=True)
    input_payload = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryRecord(Base):
    __tablename__ = "memory_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    namespace = Column(String, index=True)
    memory_type = Column(String, index=True)
    content = Column(Text)
    record_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True, nullable=True)
    agent_name = Column(String, index=True, nullable=True)
    validation_status = Column(String, index=True)
    confidence_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    groundedness_score = Column(Float, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    errors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RetryRecord(Base):
    __tablename__ = "retry_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True)
    attempt = Column(Integer, default=1)
    reason = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    status = Column(String, default="scheduled")


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True, nullable=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    labels = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, index=True)
    resource = Column(String, nullable=True)
    allowed = Column(Boolean, default=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

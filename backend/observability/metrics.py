import json
from typing import Dict, Optional

from models.schemas import PerformanceMetric, Task
from services.db_service import SessionLocal

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ModuleNotFoundError:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    Counter = Histogram = generate_latest = None


if Counter and Histogram:
    task_counter = Counter("flowiq_tasks_total", "Tasks by terminal status", ["status"])
    task_latency = Histogram("flowiq_task_latency_seconds", "Task execution latency")
    tool_latency = Histogram("flowiq_tool_latency_ms", "Tool execution latency", ["tool_name"])
else:
    task_counter = task_latency = tool_latency = None


def record_metric(metric_name: str, metric_value: float, task_id: Optional[int] = None, labels: Optional[Dict] = None):
    db = SessionLocal()
    try:
        db.add(
            PerformanceMetric(
                task_id=task_id,
                metric_name=metric_name,
                metric_value=metric_value,
                labels=json.dumps(labels or {}, default=str),
            )
        )
        db.commit()
    finally:
        db.close()


def record_task_completion(status: str, latency_seconds: Optional[float], task_id: Optional[int] = None):
    if task_counter:
        task_counter.labels(status=status).inc()
    if task_latency and latency_seconds is not None:
        task_latency.observe(latency_seconds)
    if latency_seconds is not None:
        record_metric("task_latency_seconds", latency_seconds, task_id, {"status": status})


def record_tool_latency(tool_name: str, latency_ms: float, task_id: Optional[int] = None):
    if tool_latency:
        tool_latency.labels(tool_name=tool_name).observe(latency_ms)
    record_metric("tool_latency_ms", latency_ms, task_id, {"tool_name": tool_name})


def metrics_payload():
    if generate_latest:
        return generate_latest(), CONTENT_TYPE_LATEST

    db = SessionLocal()
    try:
        total = db.query(Task).count()
        completed = db.query(Task).filter(Task.status == "completed").count()
        failed = db.query(Task).filter(Task.status == "failed").count()
        lines = [
            "# HELP flowiq_tasks_total Tasks by status",
            "# TYPE flowiq_tasks_total counter",
            f'flowiq_tasks_total{{status="all"}} {total}',
            f'flowiq_tasks_total{{status="completed"}} {completed}',
            f'flowiq_tasks_total{{status="failed"}} {failed}',
        ]
        return "\n".join(lines).encode("utf-8"), CONTENT_TYPE_LATEST
    finally:
        db.close()

from datetime import datetime

from core.config import settings
from events.dispatcher import publish_event
from events.events import EventType
from models.schemas import RetryRecord, Task
from orchestration.state_machine import TaskState


class RetryManager:
    def can_retry(self, task: Task) -> bool:
        max_retries = task.max_retries if task.max_retries is not None else settings.DEFAULT_MAX_RETRIES
        return (task.retry_count or 0) < max_retries

    def schedule_retry(self, db, task: Task, reason: str):
        task.retry_count = (task.retry_count or 0) + 1
        task.state = TaskState.RETRYING.value
        task.status = "running"
        task.updated_at = datetime.utcnow()

        record = RetryRecord(
            task_id=task.id,
            attempt=task.retry_count,
            reason=reason,
            status="scheduled",
        )
        db.add(task)
        db.add(record)
        db.commit()

        publish_event(
            EventType.RETRY_TRIGGERED,
            task_id=task.id,
            workflow_id=task.workflow_id,
            payload={"attempt": task.retry_count, "reason": reason},
        )
        return record


retry_manager = RetryManager()


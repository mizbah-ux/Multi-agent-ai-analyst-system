import json
from typing import Optional

from core.config import settings
from events.events import EventType, PlatformEvent
from models.schemas import EventLog
from services.db_service import SessionLocal

try:
    import redis
except ModuleNotFoundError:
    redis = None


class EventDispatcher:
    def __init__(self, queue_name: str = "platform:events"):
        self.queue_name = queue_name
        self._redis = None
        if settings.ENABLE_REDIS_QUEUE and redis is not None:
            try:
                self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def publish(self, event: PlatformEvent) -> PlatformEvent:
        payload = event.model_dump(mode="json")
        if self._redis:
            self._redis.lpush(self.queue_name, json.dumps(payload))

        db = SessionLocal()
        try:
            db.add(
                EventLog(
                    event_type=event.event_type.value,
                    task_id=event.task_id,
                    workflow_id=event.workflow_id,
                    payload=json.dumps(event.payload, default=str),
                    status="published",
                )
            )
            db.commit()
        finally:
            db.close()

        return event

    def pop(self, timeout_seconds: int = 1) -> Optional[PlatformEvent]:
        if not self._redis:
            return None
        item = self._redis.brpop(self.queue_name, timeout=timeout_seconds)
        if not item:
            return None
        _, raw = item
        return PlatformEvent.model_validate_json(raw)


dispatcher = EventDispatcher()


def publish_event(
    event_type: EventType,
    task_id: Optional[int] = None,
    workflow_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> PlatformEvent:
    event = PlatformEvent(
        event_type=event_type,
        task_id=task_id,
        workflow_id=workflow_id,
        payload=payload or {},
    )
    return dispatcher.publish(event)

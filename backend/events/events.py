from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RETRY_TRIGGERED = "RETRY_TRIGGERED"


class PlatformEvent(BaseModel):
    event_type: EventType
    task_id: Optional[int] = None
    workflow_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


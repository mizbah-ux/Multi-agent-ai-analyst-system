from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


ALLOWED_TRANSITIONS = {
    TaskState.PENDING: {TaskState.PLANNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.PLANNING: {
        TaskState.WAITING_FOR_TOOL,
        TaskState.EXECUTING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.WAITING_FOR_TOOL: {
        TaskState.EXECUTING,
        TaskState.RETRYING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.EXECUTING: {
        TaskState.WAITING_FOR_TOOL,
        TaskState.VALIDATING,
        TaskState.RETRYING,
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.VALIDATING: {
        TaskState.WAITING_FOR_TOOL,
        TaskState.COMPLETED,
        TaskState.RETRYING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.RETRYING: {
        TaskState.WAITING_FOR_TOOL,
        TaskState.EXECUTING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.FAILED: {TaskState.RETRYING},
    TaskState.COMPLETED: set(),
    TaskState.CANCELLED: set(),
}


STATUS_BY_STATE = {
    TaskState.PENDING: "pending",
    TaskState.PLANNING: "running",
    TaskState.WAITING_FOR_TOOL: "running",
    TaskState.EXECUTING: "running",
    TaskState.VALIDATING: "running",
    TaskState.RETRYING: "running",
    TaskState.FAILED: "failed",
    TaskState.COMPLETED: "completed",
    TaskState.CANCELLED: "cancelled",
}


def normalize_state(value: Optional[str]) -> TaskState:
    if not value:
        return TaskState.PENDING
    value = str(value).upper()
    if value == "RUNNING":
        return TaskState.EXECUTING
    if value in {"DONE", "SUCCESS"}:
        return TaskState.COMPLETED
    if value == "ERROR":
        return TaskState.FAILED
    return TaskState(value) if value in TaskState.__members__ else TaskState.PENDING


def validate_transition(current: Optional[str], next_state: TaskState) -> bool:
    current_state = normalize_state(current)
    if current_state == next_state:
        return True
    return next_state in ALLOWED_TRANSITIONS[current_state]

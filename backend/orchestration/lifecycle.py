from datetime import datetime
from typing import Optional

from fastapi import HTTPException

from models.schemas import AgentLifecycle, Task
from orchestration.state_machine import STATUS_BY_STATE, TaskState, validate_transition


def transition_task(db, task: Task, next_state: TaskState, error_message: Optional[str] = None):
    if not validate_transition(task.state or task.status, next_state):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid task transition from {task.state or task.status} to {next_state.value}",
        )

    now = datetime.utcnow()
    task.state = next_state.value
    task.status = STATUS_BY_STATE[next_state]
    task.updated_at = now

    if next_state == TaskState.EXECUTING and not task.started_at:
        task.started_at = now
    if next_state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}:
        task.completed_at = now
    if error_message:
        task.error_message = error_message

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def record_agent_state(
    db,
    task_id: int,
    agent_name: str,
    state: TaskState,
    confidence_score: Optional[float] = None,
    reasoning_summary: Optional[str] = None,
    validation_status: Optional[str] = None,
):
    now = datetime.utcnow()
    record = (
        db.query(AgentLifecycle)
        .filter(
            AgentLifecycle.task_id == task_id,
            AgentLifecycle.agent_name == agent_name,
        )
        .first()
    )
    if not record:
        record = AgentLifecycle(
            task_id=task_id,
            agent_name=agent_name,
            started_at=now if state == TaskState.EXECUTING else None,
        )

    record.state = state.value
    record.updated_at = now
    record.confidence_score = confidence_score
    record.reasoning_summary = reasoning_summary
    record.validation_status = validation_status

    if state == TaskState.EXECUTING and not record.started_at:
        record.started_at = now
    if state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}:
        record.completed_at = now

    db.add(record)
    db.commit()
    return record

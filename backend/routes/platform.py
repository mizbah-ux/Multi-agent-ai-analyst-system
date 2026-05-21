from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user
from memory.retrieval_service import retrieval_service
from models.schemas import AgentLifecycle, EventLog, EvaluationRecord, Task
from orchestration.service import orchestration_service
from security.audit import audit_event
from services.db_service import SessionLocal
from tools.execution_engine import tool_execution_engine
from tools.registry import tool_registry

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/architecture")
def architecture():
    return {
        "name": "FlowIQ",
        "workflow_graph": orchestration_service.workflow_graph(),
        "memory_layers": ["redis_short_term", "semantic_vector_memory", "postgres_structured_memory"],
        "events": [
            "TASK_CREATED",
            "TASK_ASSIGNED",
            "TASK_COMPLETED",
            "TASK_FAILED",
            "VALIDATION_FAILED",
            "RETRY_TRIGGERED",
        ],
        "task_states": [
            "PENDING",
            "PLANNING",
            "WAITING_FOR_TOOL",
            "EXECUTING",
            "VALIDATING",
            "RETRYING",
            "FAILED",
            "COMPLETED",
            "CANCELLED",
        ],
    }


@router.get("/tools")
def list_tools(current_user=Depends(get_current_user)):
    audit_event(current_user.id, "tools:list", "tool_registry")
    return [tool.model_dump() for tool in tool_registry.list_tools()]


@router.post("/tools/execute")
def execute_tool(data: dict, current_user=Depends(get_current_user)):
    tool_name = data.get("tool_name")
    payload = data.get("payload") or {}
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name required")

    role_permissions = {
        "admin": {
            "tool:data",
            "tool:analysis",
            "tool:visualization",
            "tool:reporting",
            "tool:retrieval",
        },
        "user": {
            "tool:data",
            "tool:analysis",
            "tool:visualization",
            "tool:reporting",
            "tool:retrieval",
        },
    }
    permissions = role_permissions.get(current_user.role, set())
    result = tool_execution_engine.execute(tool_name, payload, user_permissions=permissions)
    audit_event(
        current_user.id,
        "tools:execute",
        tool_name,
        allowed=result.status == "completed",
        detail={"status": result.status, "error": result.error},
    )
    return result.model_dump()


@router.post("/memory/search")
def search_memory(data: dict, current_user=Depends(get_current_user)):
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    namespace = data.get("namespace") or retrieval_service.user_namespace(current_user.id)
    limit = int(data.get("limit") or 5)
    audit_event(current_user.id, "memory:search", namespace)
    return {"results": retrieval_service.search(query, namespace=namespace, limit=limit)}


@router.get("/workflow/{task_id}/state")
def workflow_state(task_id: int, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        agents = (
            db.query(AgentLifecycle)
            .filter(AgentLifecycle.task_id == task_id)
            .order_by(AgentLifecycle.id.asc())
            .all()
        )
        events = (
            db.query(EventLog)
            .filter(EventLog.task_id == task_id)
            .order_by(EventLog.id.asc())
            .all()
        )
        evaluations = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.task_id == task_id)
            .order_by(EvaluationRecord.id.asc())
            .all()
        )
        return {
            "task": {
                "id": task.id,
                "status": task.status,
                "state": task.state,
                "retry_count": task.retry_count,
                "confidence_score": task.confidence_score,
                "validation_status": task.validation_status,
                "workflow_id": task.workflow_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            },
            "agents": [
                {
                    "agent_name": item.agent_name,
                    "state": item.state,
                    "confidence_score": item.confidence_score,
                    "validation_status": item.validation_status,
                    "reasoning_summary": item.reasoning_summary,
                }
                for item in agents
            ],
            "events": [
                {
                    "event_type": item.event_type,
                    "payload": item.payload,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in events
            ],
            "evaluations": [
                {
                    "agent_name": item.agent_name,
                    "validation_status": item.validation_status,
                    "confidence_score": item.confidence_score,
                    "reasoning_summary": item.reasoning_summary,
                }
                for item in evaluations
            ],
        }
    finally:
        db.close()

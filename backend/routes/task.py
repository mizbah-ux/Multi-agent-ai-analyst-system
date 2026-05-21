from fastapi import APIRouter, HTTPException, Depends
from services.db_service import SessionLocal
from models.schemas import Task
import json
import threading
from datetime import datetime
from auth.dependencies import get_current_user
from models.schemas import User
from services.pipeline_service import run_pipeline
from services.log_service import log_event
from core.config import settings
router = APIRouter()
#N8N_WEBHOOK = "http://localhost:5678/webhook/task-trigger"


def _run_task_pipeline(task_id: int, file_id: str, user_input: str, user_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        db.close()
        return

    try:
        run_pipeline(task_id, file_id, user_request=user_input, user_id=user_id)
    except Exception as e:
        task.status = "failed"
        task.state = "FAILED"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        db.commit()
        log_event(task_id, "Orchestrator", f"Pipeline failed: {str(e)}", "failed")
    finally:
        db.close()


@router.post("/task/create")
def create_task(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    user_input = data.get("user_input")
    file_id = data.get("file_id")

    if not user_input:
        raise HTTPException(status_code=400, detail="user_input required")
    if not file_id:
        raise HTTPException(status_code=400, detail="file_id required")

    db = SessionLocal()
    task = Task(
        user_id=current_user.id,
        user_input=user_input,
        file_id=file_id,
        status="pending",
        state="PENDING",
        retry_count=0,
        max_retries=settings.DEFAULT_MAX_RETRIES,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    worker = threading.Thread(
        target=_run_task_pipeline,
        args=(task.id, file_id, user_input, current_user.id),
        daemon=True
    )
    worker.start()

    db.close()

    return {
        "task_id": task.id,
        "status": task.status,
        "state": task.state
    }

@router.get("/task/{task_id}/result")
def get_result(
    task_id: int,
    current_user=Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = SessionLocal()
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = task.result_path
    db.close()

    return {
        "result": result,
        "download_url": f"/download/{task_id}/pdf" if task.result_path else None,
        "ppt_url": f"/download/{task_id}/ppt" if task.ppt_path else None
    }


@router.post("/task/{task_id}/complete")
def complete_task(
    task_id: int
):

    db = SessionLocal()

    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.status = "completed"
    task.state = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    db.commit()

    db.close()

    return {
        "message": "Task completed"
    }


@router.get("/task/{task_id}/status")
def get_task_status(
    task_id: int,
    current_user=Depends(get_current_user)
):

    db = SessionLocal()

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    status = task.status
    state = task.state
    retry_count = task.retry_count
    validation_status = task.validation_status
    confidence_score = task.confidence_score

    db.close()

    return {
        "status": status,
        "state": state,
        "retry_count": retry_count,
        "validation_status": validation_status,
        "confidence_score": confidence_score
    }

@router.get("/task/{task_id}/analysis")
def get_analysis(
    task_id: int,
    current_user=Depends(get_current_user)
):

    db = SessionLocal()

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if not task.result_path:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    with open(task.result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db.close()

    return data

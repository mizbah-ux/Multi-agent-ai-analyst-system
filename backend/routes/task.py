from fastapi import APIRouter, HTTPException , Depends
from services.db_service import SessionLocal
from models.schemas import Task
import requests
from auth.dependencies import get_current_user
from models.schemas import User

router = APIRouter()

N8N_WEBHOOK = "http://localhost:5678/webhook-test/run-task"


@router.post("/task/create")
def create_task(
    data: dict,
    current_user: User = Depends(
        get_current_user
    )):
    user_input = data.get("user_input")
    file_id = data.get("file_id")

    if not user_input:
        raise HTTPException(status_code=400, detail="user_input required")

    db = SessionLocal()

    task = Task(
        user_id=current_user.id,
        user_input=user_input,
        file_id=file_id,
        status="pending"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # ✅ CALL n8n HERE (after task exists)
    try:
        requests.post(N8N_WEBHOOK, json={
            "task_id": task.id,
            "file_id": file_id
        })
    except Exception as e:
        print("n8n trigger failed:", e)

    db.close()

    return {
        "task_id": task.id,
        "status": task.status
    }

@router.get("/task/{task_id}/result")
def get_result(task_id: int):
    from services.db_service import SessionLocal
    from models.schemas import Task

    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    db.close()

    if not task or not task.result_path:
        return {"result": "Task not found or result not ready"}

    return {
    "result": "Report ready",

    "download_url": f"/download?path={task.result_path}" 
        if task.result_path else None,

    "ppt_url": f"/download?path={task.ppt_path}" 
        if task.ppt_path else None
}
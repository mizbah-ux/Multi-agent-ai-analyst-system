from fastapi import APIRouter , HTTPException , Depends
from services.db_service import SessionLocal
from models.schemas import Task
from auth.dependencies import (get_current_user)
from models.schemas import User

router = APIRouter()

@router.get("/tasks")
def get_tasks(
        current_user: User = Depends(
            get_current_user
        )
    ):
    db = SessionLocal()
    tasks = db.query(Task).filter(
        Task.user_id == current_user.id
    ).all()
    db.close()

    return [
    {
        "id": t.id,
        "input": t.user_input,
        "status": t.status,
        "state": t.state,
        "confidence": t.confidence_score,
        "validation_status": t.validation_status,
        "result": t.result_path,
        "ppt": t.ppt_path
    }
    for t in tasks
    ]

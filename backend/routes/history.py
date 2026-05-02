from fastapi import APIRouter
from services.db_service import SessionLocal
from models.schemas import Task

router = APIRouter()

@router.get("/tasks")
def get_tasks():
    db = SessionLocal()
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    db.close()

    return [
    {
        "id": t.id,
        "input": t.user_input,
        "status": t.status,
        "result": t.result_path,
        "ppt": t.ppt_path
    }
    for t in tasks
    ]
from fastapi import APIRouter
from services.db_service import SessionLocal
from models.schemas import Log

router = APIRouter()


@router.get("/task/{task_id}/logs")
def get_logs(task_id: int):
    db = SessionLocal()
    logs = db.query(Log).filter(Log.task_id == task_id).all()
    db.close()
    print("TASK ID:", task_id)
    print("LOG COUNT:", len(logs))

    return [
        {
            "agent": log.agent,
            "message": log.message,
            "status": log.status,
            "time": log.timestamp
        }
        for log in logs
        
    ]

@router.post("/log")
def create_log(data: dict):
    from services.log_service import log_event

    log_event(
        data["task_id"],
        data["agent"],
        data["message"],
        data["status"]
    )

    return {"status": "logged"}
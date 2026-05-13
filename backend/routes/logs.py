from fastapi import APIRouter , HTTPException, Depends, Header
from auth.dependencies import get_current_user
from services.db_service import SessionLocal
from models.schemas import Log

router = APIRouter()


@router.get("/task/{task_id}/logs")
def get_logs(
    task_id: int,
    current_user=Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = SessionLocal()
    from models.schemas import Task

    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task or task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        logs = db.query(Log).filter(Log.task_id == task_id).order_by(Log.id.asc()).all()

        return {
            "logs": [
                {
                    "task_id": log.task_id,
                    "agent": log.agent,
                    "message": log.message,
                    "status": log.status,
                    "time": log.timestamp.isoformat() if log.timestamp else None
                }
                for log in logs
            ]
        }
    finally:
        db.close()


INTERNAL_API_KEY = "internal-secret"

@router.post("/log")
def create_log(
    data: dict,
    x_internal_key: str = Header(None)
):
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    task_id = data.get("task_id")
    agent = data.get("agent")
    message = data.get("message")
    status = data.get("status")

    if not task_id or not agent or not message or not status:
        raise HTTPException(status_code=400, detail="Missing log fields")

    db = SessionLocal()
    try:
        log = Log(
            task_id=task_id,
            agent=agent,
            message=message,
            status=status
        )
        db.add(log)
        db.commit()

        return {"message": "Log saved"}
    finally:
        db.close()

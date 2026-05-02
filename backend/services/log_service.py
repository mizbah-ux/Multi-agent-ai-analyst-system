from services.db_service import SessionLocal
from models.schemas import Log


def log_event(task_id, agent, message, status):
    db = SessionLocal()

    log = Log(
        task_id=task_id,
        agent=agent,
        message=message,
        status=status
    )

    db.add(log)
    db.commit()
    db.close()

    
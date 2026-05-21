from services.db_service import SessionLocal
from models.schemas import Log
from observability.structured_logging import get_logger

logger = get_logger("flowiq.agent")


def log_event(task_id, agent, message, status):
    db = SessionLocal()
    logger.info(
        message,
        extra={
            "extra_fields": {
                "task_id": task_id,
                "agent": agent,
                "status": status,
            }
        },
    )

    log = Log(
        task_id=task_id,
        agent=agent,
        message=message,
        status=status
    )

    db.add(log)
    db.commit()
    db.close()

    

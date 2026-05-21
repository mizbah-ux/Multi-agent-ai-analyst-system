import json

from models.schemas import AuditLog
from services.db_service import SessionLocal


def audit_event(user_id, action: str, resource=None, allowed: bool = True, detail=None):
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                allowed=allowed,
                detail=json.dumps(detail, default=str) if isinstance(detail, (dict, list)) else detail,
            )
        )
        db.commit()
    finally:
        db.close()

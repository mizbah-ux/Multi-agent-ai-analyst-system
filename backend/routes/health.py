from fastapi import APIRouter
from sqlalchemy import text

from services.db_service import engine

router = APIRouter()


@router.get("/health")
def health_check():

    db_status = "ok"

    try:

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "service": "AI Analyst Backend",
        "version": "2.0"
    }
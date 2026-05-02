from fastapi import APIRouter, HTTPException
from agents.report_agent import generate_report
from services.db_service import SessionLocal
from models.schemas import Task

router = APIRouter()


@router.post("/agent/report")
def report(data: dict):
    file_id = data.get("file_id")
    task_id = data.get("task_id")
    analysis = data.get("analysis")
    charts = data.get("charts")

    if not file_id or not task_id:
        raise HTTPException(status_code=400, detail="Missing file_id or task_id")

    try:
        result = generate_report(
            file_id,
            analysis,
            charts or []
        )
    
        db = SessionLocal()
    
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .first()
        )
    
        if task:
            task.result_path = result["report_path"]
            task.ppt_path = result.get("ppt_path")
            task.status = "completed"
    
            db.commit()
    
        db.close()
    
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
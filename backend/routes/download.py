from fastapi import (APIRouter,Depends,HTTPException)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from auth.dependencies import (get_current_user)
from models.schemas import (Task,User)
from services.db_service import (SessionLocal)

router = APIRouter()


@router.get("/download/{task_id}/{file_type}")
def download_report(
    task_id: int,
    file_type: str,
    current_user: User = Depends(
        get_current_user
    )
):

    db: Session = SessionLocal()

    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()

        if not task:

            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        file_path = None

        if file_type == "pdf":
            candidates = [
                task.result_path,
                f"reports/{task.id}_report.pdf",
                f"reports/{task.file_id}_report.pdf" if task.file_id else None
            ]
            for candidate in candidates:
                if candidate and candidate.lower().endswith(".pdf") and os.path.exists(candidate):
                    file_path = candidate
                    break

        elif file_type == "ppt":
            if task.ppt_path and os.path.exists(task.ppt_path):
                file_path = task.ppt_path

        else:

            raise HTTPException(
                status_code=400,
                detail="Invalid file type"
            )

        if not file_path:

            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        return FileResponse(file_path)
    finally:
        db.close()

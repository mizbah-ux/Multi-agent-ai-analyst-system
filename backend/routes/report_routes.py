from fastapi import APIRouter, HTTPException , Depends
from auth.dependencies import get_optional_user
from agents.report_agent import generate_report
from services.db_service import SessionLocal
from models.schemas import Task
from auth.dependencies import verify_internal_key

router = APIRouter()


@router.post("/agent/report")
def report(
    data: dict,
    _ = Depends(verify_internal_key)
):
    result = generate_report(
        data["file_id"],
        data["analysis"],
        data["charts"],
        user_request=data.get("user_request")
    )
    return {"result": result}

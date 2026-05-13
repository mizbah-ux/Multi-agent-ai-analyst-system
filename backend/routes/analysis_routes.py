from fastapi import APIRouter, HTTPException , Depends
from auth.dependencies import get_optional_user
from agents.analysis_agent import run_analysis
from auth.dependencies import verify_internal_key

router = APIRouter()


@router.post("/agent/analyze")
def analyze(
    data: dict,
    _ = Depends(verify_internal_key)
):

    result = run_analysis(
        data["file_id"],
        user_request=data.get("user_request")
    )
    return {"result": result}

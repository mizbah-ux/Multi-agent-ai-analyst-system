from fastapi import APIRouter, HTTPException
from agents.analysis_agent import run_analysis

router = APIRouter()


@router.post("/agent/analyze")
def analyze(data: dict):
    file_id = data.get("file_id")

    if not file_id:
        raise HTTPException(status_code=400, detail="file_id required")

    try:
        result = run_analysis(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
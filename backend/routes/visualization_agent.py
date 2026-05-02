from fastapi import APIRouter, HTTPException
from agents.visualization_agent import run_visualization

router = APIRouter()


@router.post("/agent/visualize")
def visualize(data: dict):
    file_id = data.get("file_id")

    if not file_id:
        raise HTTPException(status_code=400, detail="file_id required")

    try:
        result = run_visualization(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
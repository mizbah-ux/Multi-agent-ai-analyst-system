from fastapi import APIRouter, HTTPException , Depends
from agents.visualization_agent import run_visualization
from auth.dependencies import get_optional_user
from auth.dependencies import verify_internal_key

router = APIRouter()


@router.post("/agent/visualize")
def visualize(
    data: dict,
    _ = Depends(verify_internal_key)
):
    result = run_visualization(
        data["file_id"]
    )
    return {
        "result": result
    }
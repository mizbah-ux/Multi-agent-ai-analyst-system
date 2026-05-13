from fastapi import APIRouter, HTTPException , Depends
from auth.dependencies import get_optional_user
from agents.data_agent import run_data_cleaning
from auth.dependencies import get_current_user
from models.schemas import User
from auth.dependencies import verify_internal_key


router = APIRouter()


@router.post("/agent/data-clean")
def data_clean(
    data: dict,
    _ = Depends(verify_internal_key)
):

    try:
        result = run_data_cleaning(data["file_id"])
        return {"result": result}
    except Exception as e:
        print("DATA CLEANING ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
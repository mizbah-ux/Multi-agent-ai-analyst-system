from fastapi import APIRouter, HTTPException
from agents.data_agent import run_data_cleaning

router = APIRouter()


@router.post("/agent/data-clean")
def data_clean(data: dict):
    print("DEBUG INPUT:", data)   # 👈 ADD THIS

    file_id = data.get("file_id")

    if not file_id:
        raise HTTPException(status_code=400, detail="file_id required")

    try:
        result = run_data_cleaning(file_id)
        return result
    except Exception as e:
        print("ERROR:", str(e))   # 👈 ADD THIS
        print("Incoming request:", data)
        print("DATA NODE INPUT:", data)
        raise HTTPException(status_code=500, detail=str(e))
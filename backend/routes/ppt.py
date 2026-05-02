from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

# ✅ Define schema
class PPTRequest(BaseModel):
    file_id: str
    charts: List[str]


@router.post("/agent/ppt")
def create_ppt(data: PPTRequest):
    file_id = data.file_id
    charts = data.charts

    print("FINAL DEBUG:", file_id, charts)

    if not file_id:
        raise HTTPException(status_code=400, detail="file_id missing")

    if not charts:
        raise HTTPException(status_code=400, detail="charts missing")

    from services.ppt_service import generate_ppt

    try:
        result = generate_ppt(file_id, charts)
        return result
    except Exception as e:
        print("PPT ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
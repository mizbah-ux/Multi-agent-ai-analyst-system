from fastapi import APIRouter, UploadFile, File, HTTPException , Depends
import os
import uuid
import pandas as pd
from auth.dependencies import (get_current_user)
from models.schemas import User

router = APIRouter()

UPLOAD_DIR = "uploads"

# ensure folder exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        current_user: User = Depends(
            get_current_user
        )
    ):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = file.filename.split(".")[-1].lower()

    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{file_id}.{file_ext}"

    content = await file.read()

    # size limit (10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    # save file
    with open(file_path, "wb") as f:
        f.write(content)

    # basic validation
    try:
        if file_ext == "csv":
            df = pd.read_csv(file_path)
        elif file_ext == "xlsx":
            df = pd.read_excel(file_path)
        else:
            df = pd.read_json(file_path)

        if df.empty:
            raise ValueError("Empty dataset")

    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns)
    }
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

ALLOWED_DIRS = ["reports"]


@router.get("/download")
def download_file(path: str):

    normalized = os.path.normpath(path)

    if ".." in normalized:
        raise HTTPException(
            status_code=403,
            detail="Invalid path"
        )

    allowed = any(
        normalized.startswith(directory)
        for directory in ALLOWED_DIRS
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    if not os.path.exists(normalized):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        normalized,
        filename=os.path.basename(normalized)
    )
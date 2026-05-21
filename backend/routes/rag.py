import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth.dependencies import get_current_user
from memory.retrieval_service import retrieval_service
from security.audit import audit_event

router = APIRouter(prefix="/rag", tags=["rag"])

RAG_UPLOAD_DIR = Path("rag_uploads")
RAG_UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    file_id = str(uuid.uuid4())
    path = RAG_UPLOAD_DIR / f"{file_id}{ext}"
    with open(path, "wb") as handle:
        handle.write(content)

    try:
        namespace = retrieval_service.user_namespace(current_user.id)
        records = retrieval_service.ingest_file(
            str(path),
            namespace=namespace,
            metadata={"uploaded_by": current_user.id, "original_filename": file.filename},
        )
    except Exception as exc:
        os.remove(path)
        raise HTTPException(status_code=400, detail=str(exc))

    audit_event(current_user.id, "rag:ingest", str(path), detail={"chunks": len(records)})
    return {
        "file_id": file_id,
        "filename": file.filename,
        "chunks_indexed": len(records),
        "namespace": namespace,
    }


@router.post("/search")
def search(data: dict, current_user=Depends(get_current_user)):
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    namespace = data.get("namespace") or retrieval_service.user_namespace(current_user.id)
    return {
        "results": retrieval_service.search(
            query,
            namespace=namespace,
            limit=int(data.get("limit") or 5),
        )
    }


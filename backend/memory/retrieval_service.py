from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from memory.embedding_pipeline import embedding_pipeline
from memory.semantic import semantic_memory


class RetrievalService:
    def ingest_file(
        self,
        file_path: str,
        namespace: str = "global",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        path = Path(file_path)
        text = self._extract_text(path)
        return embedding_pipeline.index_text(
            text,
            namespace=namespace,
            metadata={
                "source_path": str(path),
                "filename": path.name,
                **(metadata or {}),
            },
            memory_type="document",
        )

    def index_task_summary(
        self,
        task_id: int,
        user_id: Optional[int],
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        namespace = self.user_namespace(user_id)
        return embedding_pipeline.index_text(
            summary,
            namespace=namespace,
            metadata={"task_id": task_id, **(metadata or {})},
            memory_type="task_history",
        )

    def search(self, query: str, namespace: Optional[str] = None, limit: int = 5):
        return semantic_memory.search(query=query, namespace=namespace, limit=limit)

    def retrieve_for_task(self, user_request: str, user_id: Optional[int], limit: int = 5):
        return self.search(user_request, namespace=self.user_namespace(user_id), limit=limit)

    @staticmethod
    def user_namespace(user_id: Optional[int]) -> str:
        return f"user:{user_id}" if user_id else "global"

    def _extract_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(path)
            return df.head(200).to_csv(index=False)
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except ModuleNotFoundError as exc:
                raise RuntimeError("Install pypdf to ingest PDF documents") from exc
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if suffix == ".docx":
            try:
                from docx import Document
            except ModuleNotFoundError as exc:
                raise RuntimeError("Install python-docx to ingest DOCX documents") from exc
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise RuntimeError(f"Unsupported RAG file type: {suffix}")


retrieval_service = RetrievalService()

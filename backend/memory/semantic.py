import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import settings
from models.schemas import MemoryRecord
from services.db_service import SessionLocal

try:
    from sklearn.feature_extraction.text import HashingVectorizer
except ModuleNotFoundError:
    HashingVectorizer = None


class SemanticMemory:
    """Local semantic store with a Chroma-compatible service boundary.

    The default implementation uses a deterministic hashing vectorizer so the
    app works without external services. ChromaDB can be added behind this same
    interface later by switching VECTOR_BACKEND.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or settings.SEMANTIC_MEMORY_PATH)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._vectorizer = (
            HashingVectorizer(n_features=512, alternate_sign=False, norm="l2")
            if HashingVectorizer
            else None
        )

    def add(
        self,
        content: str,
        namespace: str = "global",
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "semantic",
    ) -> Dict[str, Any]:
        content = (content or "").strip()
        if not content:
            return {}

        record = {
            "id": self._next_id(),
            "namespace": namespace,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        records = self._load()
        records.append(record)
        self._save(records)
        self._record_relational_memory(record)
        return record

    def search(self, query: str, namespace: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        records = [
            record
            for record in self._load()
            if not namespace or record.get("namespace") == namespace
        ]
        if not records:
            return []

        scores = self._score(query, [record.get("content", "") for record in records])
        ranked = sorted(zip(records, scores), key=lambda item: item[1], reverse=True)[:limit]
        return [
            {
                **record,
                "score": round(float(score), 4),
            }
            for record, score in ranked
            if score > 0
        ]

    def _score(self, query: str, docs: List[str]) -> List[float]:
        if self._vectorizer:
            matrix = self._vectorizer.transform([query] + docs)
            query_vector = matrix[0]
            doc_vectors = matrix[1:]
            raw_scores = doc_vectors @ query_vector.T
            return [float(value[0]) for value in raw_scores.toarray()]

        query_terms = set(query.lower().split())
        scores = []
        for doc in docs:
            doc_terms = set(doc.lower().split())
            if not doc_terms:
                scores.append(0.0)
                continue
            overlap = len(query_terms & doc_terms)
            denominator = math.sqrt(len(query_terms) * len(doc_terms)) or 1
            scores.append(overlap / denominator)
        return scores

    def _load(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        with open(self.storage_path, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []

    def _save(self, records: List[Dict[str, Any]]):
        tmp_path = self.storage_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.storage_path)

    def _next_id(self) -> str:
        return f"mem_{len(self._load()) + 1:08d}"

    def _record_relational_memory(self, record: Dict[str, Any]):
        db = SessionLocal()
        try:
            db.add(
                MemoryRecord(
                    namespace=record["namespace"],
                    memory_type=record["memory_type"],
                    content=record["content"],
                    record_metadata=json.dumps(record["metadata"], default=str),
                )
            )
            db.commit()
        finally:
            db.close()


semantic_memory = SemanticMemory()

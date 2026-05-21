from typing import Any, Dict, Iterable, List, Optional

from memory.semantic import semantic_memory


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 160) -> List[str]:
    clean = " ".join((text or "").split())
    if not clean:
        return []
    chunks = []
    cursor = 0
    while cursor < len(clean):
        chunks.append(clean[cursor : cursor + chunk_size])
        cursor += max(1, chunk_size - overlap)
    return chunks


class EmbeddingPipeline:
    def index_text(
        self,
        text: str,
        namespace: str = "global",
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "document",
    ) -> List[Dict[str, Any]]:
        records = []
        for index, chunk in enumerate(chunk_text(text)):
            chunk_metadata = {
                **(metadata or {}),
                "chunk_index": index,
            }
            records.append(
                semantic_memory.add(
                    chunk,
                    namespace=namespace,
                    metadata=chunk_metadata,
                    memory_type=memory_type,
                )
            )
        return [record for record in records if record]

    def index_items(
        self,
        items: Iterable[Dict[str, Any]],
        namespace: str = "global",
        memory_type: str = "execution",
    ) -> List[Dict[str, Any]]:
        indexed = []
        for item in items:
            content = item.get("content") or item.get("text") or ""
            metadata = {key: value for key, value in item.items() if key not in {"content", "text"}}
            indexed.extend(self.index_text(content, namespace, metadata, memory_type))
        return indexed


embedding_pipeline = EmbeddingPipeline()

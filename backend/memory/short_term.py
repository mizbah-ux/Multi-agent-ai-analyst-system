import json
import time
from typing import Any, Dict, List, Optional

from core.config import settings

try:
    import redis
except ModuleNotFoundError:
    redis = None


class ShortTermMemory:
    """Redis-backed session memory with an in-process fallback for local runs."""

    def __init__(self):
        self._redis = None
        self._fallback: Dict[str, Dict[str, Any]] = {}
        if redis is not None:
            try:
                self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def set_context(self, session_id: str, context: Dict[str, Any], ttl_seconds: Optional[int] = None):
        ttl = ttl_seconds or settings.SHORT_TERM_TTL_SECONDS
        payload = json.dumps(context, default=str)
        if self._redis:
            self._redis.setex(self._key(session_id), ttl, payload)
            return
        self._fallback[session_id] = {"expires_at": time.time() + ttl, "context": context}

    def get_context(self, session_id: str) -> Dict[str, Any]:
        if self._redis:
            payload = self._redis.get(self._key(session_id))
            return json.loads(payload) if payload else {}

        item = self._fallback.get(session_id)
        if not item:
            return {}
        if item["expires_at"] < time.time():
            self._fallback.pop(session_id, None)
            return {}
        return dict(item["context"])

    def append_event(self, session_id: str, event: Dict[str, Any]):
        context = self.get_context(session_id)
        events: List[Dict[str, Any]] = context.setdefault("events", [])
        events.append(event)
        self.set_context(session_id, context)

    def clear(self, session_id: str):
        if self._redis:
            self._redis.delete(self._key(session_id))
        self._fallback.pop(session_id, None)

    @staticmethod
    def _key(session_id: str) -> str:
        return f"session:{session_id}:context"


short_term_memory = ShortTermMemory()

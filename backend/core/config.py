from functools import lru_cache
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:
    BaseSettings = object
    SettingsConfigDict = dict


class Settings(BaseSettings):
    """Central runtime settings with safe local-development defaults."""

    if BaseSettings is not object:
        model_config = SettingsConfigDict(
            env_file=(".env", "backend/.env"),
            env_file_encoding="utf-8",
            extra="ignore",
        )

    APP_NAME: str = "FlowIQ"
    DATABASE_URL: str = "sqlite:///./ai_analyst.db"
    SECRET_KEY: str = "fallback-secret-key-for-development-only-change-in-production"
    REDIS_URL: str = "redis://localhost:6379/0"
    VECTOR_BACKEND: str = "local"
    CHROMA_PERSIST_DIR: str = "vector_store/chroma"
    SEMANTIC_MEMORY_PATH: str = "memory_store/semantic_memory.json"
    SHORT_TERM_TTL_SECONDS: int = 3600
    TASK_TIMEOUT_SECONDS: int = 900
    DEFAULT_MAX_RETRIES: int = 2
    RATE_LIMIT_PER_MINUTE: int = 120
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    ENABLE_LLM_JUDGE: bool = False
    ENABLE_REDIS_QUEUE: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


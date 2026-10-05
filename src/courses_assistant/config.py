"""Конфигурация приложения (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Приложение
    app_env: str = "local"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/edu_platform_kurses"
    )
    dsn: str = Field(default="postgresql://postgres:postgres@localhost:5432/edu_platform_kurses")

    # Redis Streams
    redis_url: str = "redis://localhost:6379/0"
    stream_requests: str = "rag.requests"
    stream_dead: str = "rag.dead"
    stream_events: str = "rag.events"
    consumer_group: str = "rag-workers"
    consumer_name: str = "worker-1"
    job_max_attempts: int = 3
    consumer_pending_idle_ms: int = 60_000
    stream_block_ms: int = 5000

    # Embeddings (Ollama)
    ollama_url: str = "http://localhost:11434/api/embed"
    embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = 768
    retrieval_top_k: int = 5

    # GigaChat (LLM)
    gigachat_credentials: str = Field(default="")
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    gigachat_base_url: str = "https://api.giga.chat/v1"
    gigachat_model: str = "GigaChat-2"
    gigachat_verify_ssl: bool = False
    llm_timeout: float = 120.0
    llm_temperature: float = 0.2

    def require_gigachat_credentials(self) -> str:
        if not self.gigachat_credentials:
            raise ValueError(
                "Не задан GIGACHAT_CREDENTIALS. Укажите его в окружении или .env."
            )
        return self.gigachat_credentials


@lru_cache
def get_settings() -> Settings:
    return Settings()

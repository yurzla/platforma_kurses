"""Конфигурация приложения (pydantic-settings)."""

from __future__ import annotations

import logging
import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_EPHEMERAL_JWT_SECRET: str | None = None


def _ephemeral_jwt_secret() -> str:
    global _EPHEMERAL_JWT_SECRET
    if _EPHEMERAL_JWT_SECRET is None:
        _EPHEMERAL_JWT_SECRET = secrets.token_urlsafe(32)
        logger.warning(
            "JWT_SECRET не задан: сгенерирован эфемерный секрет. "
            "Токены не переживут рестарт; задайте JWT_SECRET в проде."
        )
    return _EPHEMERAL_JWT_SECRET


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
    api_port: int = 5000

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

    # Cron (отдельная очередь периодических задач)
    stream_cron: str = "rag.cron"
    cron_dlq: str = "rag.cron.dead"
    cron_group: str = "rag-cron"
    cron_consumer_name: str = "cron-1"
    cron_interval_seconds: int = 3600
    job_retention_days: int = 7

    # Ретенция Redis-стримов
    redis_stream_maxlen: int = 10_000
    redis_stream_events_maxlen: int = 1_000

    # JWT-аутентификация (access + refresh в httpOnly cookie)
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl: int = 60 * 15
    refresh_token_ttl: int = 60 * 60 * 24 * 14
    cookie_secure: bool = False
    access_cookie: str = "access_token"
    refresh_cookie: str = "refresh_token"

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

    def resolved_jwt_secret(self) -> str:
        """Ключ подписи JWT; при отсутствии — эфемерный на процесс."""
        return self.jwt_secret or _ephemeral_jwt_secret()


@lru_cache
def get_settings() -> Settings:
    return Settings()

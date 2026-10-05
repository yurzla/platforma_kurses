"""Конфигурация web-сервиса (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "local"
    log_level: str = "INFO"
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    api_base_url: str = "http://localhost:5000"
    access_cookie: str = "access_token"
    refresh_cookie: str = "refresh_token"


@lru_cache
def get_settings() -> Settings:
    return Settings()

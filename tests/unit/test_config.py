"""Тесты конфигурации."""

from __future__ import annotations

import pytest

from courses_assistant.config import Settings


def test_require_gigachat_credentials_raises_when_missing() -> None:
    settings = Settings(gigachat_credentials="")
    with pytest.raises(ValueError, match="GIGACHAT_CREDENTIALS"):
        settings.require_gigachat_credentials()


def test_require_gigachat_credentials_returns_value() -> None:
    settings = Settings(gigachat_credentials="secret")
    assert settings.require_gigachat_credentials() == "secret"


def test_defaults() -> None:
    settings = Settings()
    assert settings.embedding_dimension == 768
    assert settings.stream_requests == "rag.requests"


def test_resolved_jwt_secret_uses_configured() -> None:
    assert Settings(jwt_secret="key").resolved_jwt_secret() == "key"


def test_resolved_jwt_secret_ephemeral_when_missing() -> None:
    settings = Settings(jwt_secret="")
    secret = settings.resolved_jwt_secret()
    assert secret
    assert secret == settings.resolved_jwt_secret()

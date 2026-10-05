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


def test_admin_auth_disabled_without_credentials() -> None:
    settings = Settings(admin_username="", admin_password="")
    assert settings.admin_auth_enabled() is False
    assert settings.verify_admin("admin", "x") is False


def test_admin_auth_enabled_only_with_both_fields() -> None:
    assert Settings(admin_username="admin", admin_password="").admin_auth_enabled() is False
    assert Settings(admin_username="", admin_password="x").admin_auth_enabled() is False
    assert Settings(admin_username="admin", admin_password="x").admin_auth_enabled() is True


def test_verify_admin() -> None:
    settings = Settings(admin_username="admin", admin_password="s3cret")
    assert settings.verify_admin("admin", "s3cret") is True
    assert settings.verify_admin("admin", "wrong") is False
    assert settings.verify_admin("nobody", "s3cret") is False


def test_session_secret_falls_back_to_credentials() -> None:
    explicit = Settings(admin_session_secret="key")
    assert explicit.session_secret() == "key"
    derived = Settings(admin_username="admin", admin_password="s3cret")
    assert len(derived.session_secret()) == 64

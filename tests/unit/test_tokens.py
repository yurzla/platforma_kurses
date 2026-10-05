"""Тесты JWT access-токенов."""

from __future__ import annotations

import jwt
import pytest

from courses_assistant.adapters.tokens.jwt import JwtTokenService
from courses_assistant.domain.errors import InvalidToken

_SECRET = "unit-test-secret-key-0123456789abcdef"


def _service(ttl: int = 900) -> JwtTokenService:
    return JwtTokenService(secret=_SECRET, algorithm="HS256", access_ttl=ttl)


def test_access_token_roundtrip() -> None:
    service = _service()
    token = service.create_access_token(42)
    assert service.decode_access_token(token) == 42


def test_expired_token_rejected() -> None:
    with pytest.raises(InvalidToken):
        _service(ttl=-1).decode_access_token(_service(ttl=-1).create_access_token(1))


def test_tampered_token_rejected() -> None:
    token = _service().create_access_token(1)
    with pytest.raises(InvalidToken):
        _service().decode_access_token(token + "x")


def test_wrong_type_rejected() -> None:
    token = jwt.encode({"sub": "1", "type": "refresh"}, _SECRET, algorithm="HS256")
    with pytest.raises(InvalidToken):
        _service().decode_access_token(token)


def test_missing_subject_rejected() -> None:
    token = jwt.encode({"type": "access"}, _SECRET, algorithm="HS256")
    with pytest.raises(InvalidToken):
        _service().decode_access_token(token)

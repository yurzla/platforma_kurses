"""Подписанные access-токены (JWT, HS256)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import jwt

from courses_assistant.application.ports import TokenService
from courses_assistant.domain.errors import InvalidToken

_ACCESS_TYPE = "access"


class JwtTokenService(TokenService):
    def __init__(self, secret: str, algorithm: str, access_ttl: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._access_ttl = access_ttl

    def create_access_token(self, user_id: int) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": _ACCESS_TYPE,
            "iat": now,
            "exp": now + timedelta(seconds=self._access_ttl),
            "jti": secrets.token_urlsafe(16),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidToken("Некорректный access-токен") from exc
        if payload.get("type") != _ACCESS_TYPE:
            raise InvalidToken("Неверный тип токена")
        subject = payload.get("sub")
        if subject is None:
            raise InvalidToken("В токене нет субъекта")
        try:
            return int(subject)
        except (TypeError, ValueError) as exc:
            raise InvalidToken("Некорректный субъект токена") from exc

"""Хэширование и проверка паролей (stdlib scrypt)."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

_ALGO = "scrypt"
_N = 2**14
_R = 8
_P = 1
_DKLEN = 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN
    )
    return f"{_ALGO}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, salt_hex, digest_hex = encoded.split("$")
    except (AttributeError, ValueError):
        return False
    if algo != _ALGO:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=len(expected)
    )
    return hmac.compare_digest(digest, expected)


def new_refresh_token() -> str:
    """Генерирует случайный opaque refresh-токен."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Возвращает sha256-хеш refresh-токена для хранения в БД."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

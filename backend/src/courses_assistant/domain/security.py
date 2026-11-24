"""Шифрование и проверка паролей (Fernet) и хеширование refresh-токенов."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, InvalidToken

_ALGO = "fernet"


def generate_password_key() -> str:
    """Генерирует urlsafe-base64 ключ Fernet для PASSWORD_KEY."""
    return Fernet.generate_key().decode("ascii")


def _fernet(key: str) -> Fernet:
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError(
            "Некорректный PASSWORD_KEY: ожидается urlsafe-base64 ключ Fernet."
        ) from exc


def encrypt_password(password: str, key: str) -> str:
    """Шифрует пароль ключом из настроек и добавляет префикс формата."""
    token = _fernet(key).encrypt(password.encode("utf-8"))
    return f"{_ALGO}${token.decode('ascii')}"


def verify_password(password: str, encoded: str, key: str) -> bool:
    """Расшифровывает сохранённый пароль и сравнивает его с введённым."""
    try:
        algo, token = encoded.split("$", 1)
    except (AttributeError, ValueError):
        return False
    if algo != _ALGO:
        return False
    try:
        decrypted = _fernet(key).decrypt(token.encode("ascii"))
    except (InvalidToken, UnicodeEncodeError):
        return False
    return hmac.compare_digest(decrypted, password.encode("utf-8"))


def new_refresh_token() -> str:
    """Генерирует случайный opaque refresh-токен."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Возвращает sha256-хеш refresh-токена для хранения в БД."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

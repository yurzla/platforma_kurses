"""Тесты обратимого шифрования паролей и настройки ключа."""

from __future__ import annotations

import pytest

from courses_assistant.config import Settings
from courses_assistant.domain.security import (
    encrypt_password,
    generate_password_key,
    verify_password,
)


def test_encryption_roundtrip() -> None:
    key = generate_password_key()
    encoded = encrypt_password("secret", key)
    assert encoded.startswith("fernet$")
    assert verify_password("secret", encoded, key) is True
    assert verify_password("other", encoded, key) is False


def test_ciphertexts_are_unique() -> None:
    key = generate_password_key()
    assert encrypt_password("secret", key) != encrypt_password("secret", key)


def test_tampered_or_foreign_value_rejected() -> None:
    key = generate_password_key()
    other_key = generate_password_key()
    encoded = encrypt_password("secret", key)
    token = encoded.removeprefix("fernet$")
    tampered = "fernet$" + token[:-4] + ("AAAA" if token[-4:] != "AAAA" else "BBBB")
    assert verify_password("secret", tampered, key) is False
    assert verify_password("secret", encoded, other_key) is False


def test_legacy_or_garbage_values_rejected() -> None:
    key = generate_password_key()
    assert verify_password("secret", "scrypt$00$00", key) is False
    assert verify_password("secret", "garbage", key) is False
    assert verify_password("secret", "", key) is False


def test_invalid_key_rejected() -> None:
    with pytest.raises(ValueError, match="PASSWORD_KEY"):
        encrypt_password("secret", "not-a-fernet-key")


def test_require_password_key() -> None:
    with pytest.raises(ValueError, match="PASSWORD_KEY"):
        Settings(_env_file=None).require_password_key()
    assert Settings(password_key="key").require_password_key() == "key"


def test_password_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    key = generate_password_key()
    monkeypatch.setenv("PASSWORD_KEY", key)
    assert Settings(_env_file=None).require_password_key() == key

"""Доменные ошибки."""

from __future__ import annotations


class DomainError(Exception):
    """Базовая доменная ошибка."""


class SessionNotFound(DomainError):
    """Чат-сессия не найдена."""


class JobNotFound(DomainError):
    """Job не найден."""


class UserNotFound(DomainError):
    """Пользователь не найден."""


class EmailAlreadyExists(DomainError):
    """Email уже зарегистрирован."""


class InvalidRole(DomainError):
    """Недопустимая роль пользователя."""


class CannotChangeOwnRole(DomainError):
    """Пользователь не может менять собственную роль."""


class CourseNotFound(DomainError):
    """Курс не найден."""


class ConfigurationError(DomainError):
    """Некорректная конфигурация."""


class ExternalServiceError(DomainError):
    """Ошибка внешнего сервиса (LLM/embeddings)."""

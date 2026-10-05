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


class CourseNotFound(DomainError):
    """Курс не найден."""


class ConfigurationError(DomainError):
    """Некорректная конфигурация."""


class ExternalServiceError(DomainError):
    """Ошибка внешнего сервиса (LLM/embeddings)."""

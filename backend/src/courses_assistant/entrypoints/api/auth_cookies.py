"""Установка и очистка JWT-cookie (access + refresh)."""

from __future__ import annotations

from fastapi import Response

from courses_assistant.config import Settings


def set_auth_cookies(
    response: Response, settings: Settings, access_token: str, refresh_token: str
) -> None:
    response.set_cookie(
        settings.access_cookie,
        access_token,
        max_age=settings.access_token_ttl,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    response.set_cookie(
        settings.refresh_cookie,
        refresh_token,
        max_age=settings.refresh_token_ttl,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.access_cookie, path="/")
    response.delete_cookie(settings.refresh_cookie, path="/")

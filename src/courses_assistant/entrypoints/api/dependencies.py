"""FastAPI-зависимости."""

from __future__ import annotations

from fastapi import HTTPException, Request

from courses_assistant.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container


def _extract_admin_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    if "admin_token" in request.cookies:
        return request.cookies["admin_token"]
    return request.query_params.get("token")


def require_admin(request: Request) -> None:
    """Проверяет admin-токен, если он задан в настройках."""
    expected = request.app.state.container.settings.admin_token
    if not expected:
        return
    if _extract_admin_token(request) != expected:
        raise HTTPException(status_code=401, detail="Требуется admin token")


def admin_token_ok(request: Request) -> bool:
    expected = request.app.state.container.settings.admin_token
    if not expected:
        return True
    return _extract_admin_token(request) == expected

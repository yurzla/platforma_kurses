"""FastAPI-зависимости API (JSON-бэкенд)."""

from __future__ import annotations

from fastapi import HTTPException, Request

from courses_assistant.container import Container

ADMIN_SESSION_KEY = "admin_user"
STUDENT_SESSION_KEY = "student_user"


def get_container(request: Request) -> Container:
    return request.app.state.container


def admin_authenticated(request: Request) -> bool:
    """Доступ разрешён, если аутентификация выключена или есть валидная сессия."""
    settings = request.app.state.container.settings
    if not settings.admin_auth_enabled():
        return True
    return bool(request.session.get(ADMIN_SESSION_KEY))


def require_admin(request: Request) -> None:
    if not admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Требуется вход администратора")


def require_student(request: Request) -> int:
    user_id = request.session.get(STUDENT_SESSION_KEY)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Требуется вход студента")
    return int(user_id)

"""FastAPI-зависимости."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import HTTPException, Request

from courses_assistant.container import Container

SESSION_KEY = "admin_user"


def get_container(request: Request) -> Container:
    return request.app.state.container


def admin_authenticated(request: Request) -> bool:
    """Доступ разрешён, если аутентификация выключена или есть валидная сессия."""
    settings = request.app.state.container.settings
    if not settings.admin_auth_enabled():
        return True
    return bool(request.session.get(SESSION_KEY))


def require_admin(request: Request) -> None:
    """Для API: 401, если вход требуется и сессии нет."""
    if not admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Требуется вход")


def require_admin_page(request: Request) -> None:
    """Для HTML-страниц: редирект на /login, если вход требуется и сессии нет."""
    if admin_authenticated(request):
        return
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    location = f"/login?next={quote(target, safe='/')}"
    raise HTTPException(status_code=307, headers={"Location": location})

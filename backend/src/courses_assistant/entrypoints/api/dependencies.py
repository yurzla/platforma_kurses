"""FastAPI-зависимости API (JSON-бэкенд)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from courses_assistant.container import Container
from courses_assistant.domain.models import User, is_admin

USER_SESSION_KEY = "user"


def get_container(request: Request) -> Container:
    return request.app.state.container


async def get_current_user(
    request: Request,
    container: Container = Depends(get_container),
) -> User | None:
    """Пользователь из сессии (или None). Роль берётся из БД на каждом запросе."""
    user_id = request.session.get(USER_SESSION_KEY)
    if user_id is None:
        return None
    async with container.uow_factory() as uow:
        return await uow.users.get(int(user_id))


async def require_user(
    request: Request,
    container: Container = Depends(get_container),
) -> User:
    user = await get_current_user(request, container)
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    return user


async def require_admin(
    request: Request,
    container: Container = Depends(get_container),
) -> User:
    user = await get_current_user(request, container)
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    if not is_admin(user.role):
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return user

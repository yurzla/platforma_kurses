"""FastAPI-зависимости API (JSON-бэкенд)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from courses_assistant.config import Settings
from courses_assistant.container import Container
from courses_assistant.domain.errors import InvalidToken
from courses_assistant.domain.models import User, UserRole, is_admin


def get_container(request: Request) -> Container:
    return request.app.state.container


def extract_access_token(request: Request, settings: Settings) -> str | None:
    """Access-токен из httpOnly cookie или заголовка `Authorization: Bearer`."""
    token = request.cookies.get(settings.access_cookie)
    if token:
        return token
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value
    return None


async def get_current_user(
    request: Request,
    container: Container = Depends(get_container),
) -> User | None:
    """Пользователь из access-токена. Роль берётся из БД на каждом запросе."""
    token = extract_access_token(request, container.settings)
    if token is None:
        return None
    try:
        user_id = container.tokens.decode_access_token(token)
    except InvalidToken:
        return None
    async with container.uow_factory() as uow:
        return await uow.users.get(user_id)


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


async def require_teacher(
    request: Request,
    container: Container = Depends(get_container),
) -> User:
    user = await get_current_user(request, container)
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    if user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Требуются права преподавателя")
    return user

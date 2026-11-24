"""Проверка доступа к объектам, привязанным к чат-сессии."""

from __future__ import annotations

from fastapi import HTTPException

from courses_assistant.container import Container
from courses_assistant.domain.models import ChatSession, User, is_admin


async def ensure_session_access(
    container: Container, session_id: int, user: User
) -> ChatSession:
    """Возвращает сессию, если доступна пользователю (владелец или админ)."""
    async with container.uow_factory() as uow:
        session = await uow.chat.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Чат-сессия не найдена")
    if session.user_id != user.id and not is_admin(user.role):
        raise HTTPException(status_code=403, detail="Нет доступа к чужой сессии")
    return session

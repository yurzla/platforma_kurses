"""Роутер чата: сессии и история сообщений (с проверкой владения)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from courses_assistant.application.commands import CreateChatSession
from courses_assistant.application.queries import get_history
from courses_assistant.container import Container
from courses_assistant.domain.models import User
from courses_assistant.entrypoints.api.dependencies import get_container, require_user
from courses_assistant.entrypoints.api.ownership import ensure_session_access
from courses_assistant.entrypoints.api.schemas import (
    MessageRead,
    SessionCreate,
    SessionListItemRead,
    SessionRead,
)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/sessions", response_model=list[SessionListItemRead])
async def list_sessions(
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> list[SessionListItemRead]:
    async with container.uow_factory() as uow:
        sessions = await uow.chat.list_sessions(user.id)
    return [
        SessionListItemRead(
            id=session.id,
            course_id=session.course_id,
            course_title=session.course_title,
            started_at=session.started_at,
            last_message=session.last_message,
        )
        for session in sessions
    ]


@router.post("/sessions", response_model=SessionRead, status_code=201)
async def create_session(
    payload: SessionCreate,
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> SessionRead:
    session_id = await container.handlers.create_session(
        CreateChatSession(user_id=user.id, course_id=payload.course_id)
    )
    return SessionRead(id=session_id, user_id=user.id, course_id=payload.course_id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
async def list_messages(
    session_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> list[MessageRead]:
    await ensure_session_access(container, session_id, user)
    history = await get_history(container.uow_factory, session_id, limit=limit)
    return [
        MessageRead(
            id=message.id,
            role=str(message.role),
            content=message.content,
            sources=message.sources,
            used_chunk_ids=message.used_chunk_ids,
            created_at=message.created_at,
        )
        for message in history
    ]

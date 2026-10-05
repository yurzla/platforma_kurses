"""Роутер чата: сессии и история сообщений."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from courses_assistant.application.commands import CreateChatSession
from courses_assistant.application.queries import get_history
from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container
from courses_assistant.entrypoints.api.schemas import MessageRead, SessionCreate, SessionRead

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionRead, status_code=201)
async def create_session(
    payload: SessionCreate,
    container: Container = Depends(get_container),
) -> SessionRead:
    session_id = await container.handlers.create_session(
        CreateChatSession(user_id=payload.user_id, course_id=payload.course_id)
    )
    return SessionRead(id=session_id, user_id=payload.user_id, course_id=payload.course_id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
async def list_messages(
    session_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    container: Container = Depends(get_container),
) -> list[MessageRead]:
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

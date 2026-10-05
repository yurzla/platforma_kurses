"""Роутер чата: сессии и история сообщений."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from courses_assistant.application.commands import CreateChatSession
from courses_assistant.application.queries import get_history
from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import (
    USER_SESSION_KEY,
    get_container,
)
from courses_assistant.entrypoints.api.schemas import MessageRead, SessionCreate, SessionRead

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _resolve_user_id(request: Request, payload_user_id: int | None) -> int:
    session_user = request.session.get(USER_SESSION_KEY)
    if session_user is not None:
        return int(session_user)
    if payload_user_id is not None:
        return payload_user_id
    raise HTTPException(status_code=401, detail="Требуется вход")


@router.post("/sessions", response_model=SessionRead, status_code=201)
async def create_session(
    payload: SessionCreate,
    request: Request,
    container: Container = Depends(get_container),
) -> SessionRead:
    user_id = _resolve_user_id(request, payload.user_id)
    session_id = await container.handlers.create_session(
        CreateChatSession(user_id=user_id, course_id=payload.course_id)
    )
    return SessionRead(id=session_id, user_id=user_id, course_id=payload.course_id)


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

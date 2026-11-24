"""Роутер чата: сессии и история сообщений (с проверкой владения)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from courses_assistant.adapters.export.pdf import render_pdf
from courses_assistant.application.chat_export import (
    DialogMeta,
    build_dialog,
    dialog_filename,
    render_markdown,
)
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

_EXPORT_LIMIT = 10_000
_EXPORT_MEDIA_TYPES = {
    "md": "text/markdown; charset=utf-8",
    "pdf": "application/pdf",
}


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


@router.delete("/sessions", status_code=204)
async def delete_all_sessions(
    course_id: int | None = Query(default=None),
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> Response:
    async with container.uow_factory() as uow:
        session_ids = await uow.chat.list_session_ids(user.id, course_id=course_id)
        await uow.jobs.delete_by_sessions(session_ids)
        await uow.chat.delete_sessions(user.id, course_id=course_id)
        await uow.commit()
    return Response(status_code=204)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> Response:
    await ensure_session_access(container, session_id, user)
    async with container.uow_factory() as uow:
        await uow.jobs.delete_by_session(session_id)
        await uow.chat.delete_session(session_id)
        await uow.commit()
    return Response(status_code=204)


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    format: str = Query(default=""),
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> Response:
    if format not in _EXPORT_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются форматы выгрузки: md, pdf",
        )
    session = await ensure_session_access(container, session_id, user)
    async with container.uow_factory() as uow:
        messages = await uow.chat.get_history(session_id, limit=_EXPORT_LIMIT)
        course_title: str | None = None
        if session.course_id is not None:
            course = await uow.catalog.get_course(session.course_id, user.id)
            course_title = course.title if course is not None else None
    participant = f"{user.name} <{user.email}>" if user.name else user.email
    meta = DialogMeta(
        session_id=session_id,
        course_title=course_title,
        started_at=session.started_at,
        participant=participant,
    )
    blocks = build_dialog(messages)
    content: str | bytes = (
        render_markdown(meta, blocks) if format == "md" else render_pdf(meta, blocks)
    )
    filename = dialog_filename(meta, format)
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

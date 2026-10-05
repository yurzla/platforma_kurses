"""Роутер job-ов: постановка вопроса и polling статуса (с проверкой владения)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from courses_assistant.application.commands import SendQuestion
from courses_assistant.application.queries import get_job
from courses_assistant.container import Container
from courses_assistant.domain.models import User, is_admin
from courses_assistant.entrypoints.api.dependencies import get_container, require_user
from courses_assistant.entrypoints.api.ownership import ensure_session_access
from courses_assistant.entrypoints.api.schemas import AskRequest, JobAccepted, JobRead

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.post("/chat/sessions/{session_id}/ask", response_model=JobAccepted, status_code=202)
async def ask(
    session_id: int,
    payload: AskRequest,
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> JobAccepted:
    await ensure_session_access(container, session_id, user)
    job_id = await container.handlers.send_question(
        SendQuestion(session_id=session_id, question=payload.question)
    )
    return JobAccepted(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobRead)
async def job_status(
    job_id: str,
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> JobRead:
    job = await get_job(container.uow_factory, job_id)
    async with container.uow_factory() as uow:
        session = await uow.chat.get_session(job.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Чат-сессия не найдена")
    if session.user_id != user.id and not is_admin(user.role):
        raise HTTPException(status_code=403, detail="Нет доступа к чужому job-у")
    return JobRead(
        id=job.id,
        session_id=job.session_id,
        status=str(job.status),
        question=job.question,
        answer=job.answer,
        sources=job.sources,
        rewritten_question=job.rewritten_question,
        error=job.error,
        attempts=job.attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )

"""Роутер job-ов: постановка вопроса и polling статуса."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from courses_assistant.application.commands import SendQuestion
from courses_assistant.application.queries import get_job
from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container
from courses_assistant.entrypoints.api.schemas import AskRequest, JobAccepted, JobRead

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.post("/chat/sessions/{session_id}/ask", response_model=JobAccepted, status_code=202)
async def ask(
    session_id: int,
    payload: AskRequest,
    container: Container = Depends(get_container),
) -> JobAccepted:
    job_id = await container.handlers.send_question(
        SendQuestion(session_id=session_id, question=payload.question)
    )
    return JobAccepted(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobRead)
async def job_status(
    job_id: str,
    container: Container = Depends(get_container),
) -> JobRead:
    job = await get_job(container.uow_factory, job_id)
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

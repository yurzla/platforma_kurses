"""Query-обработчики (чтение)."""

from __future__ import annotations

from collections.abc import Callable

from courses_assistant.application.ports import UnitOfWork
from courses_assistant.domain.errors import JobNotFound, SessionNotFound
from courses_assistant.domain.models import ChatMessage, QuestionJob


async def get_history(
    uow_factory: Callable[[], UnitOfWork],
    session_id: int,
    limit: int,
) -> list[ChatMessage]:
    async with uow_factory() as uow:
        session = await uow.chat.get_session(session_id)
        if session is None:
            raise SessionNotFound(f"Чат-сессия {session_id} не найдена.")
        return await uow.chat.get_history(session_id, limit=limit)


async def get_job(
    uow_factory: Callable[[], UnitOfWork],
    job_id: str,
) -> QuestionJob:
    async with uow_factory() as uow:
        job = await uow.jobs.get(job_id)
        if job is None:
            raise JobNotFound(f"Job {job_id} не найден.")
        return job

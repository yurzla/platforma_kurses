"""Query-обработчики (чтение)."""

from __future__ import annotations

from collections.abc import Callable

from courses_assistant.application.ports import MessageBroker, UnitOfWork
from courses_assistant.domain.errors import JobNotFound, SessionNotFound
from courses_assistant.domain.models import ChatMessage, JobStatus, QuestionJob


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


async def list_jobs(
    uow_factory: Callable[[], UnitOfWork],
    *,
    status: JobStatus | None = None,
    session_id: int | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[QuestionJob], int]:
    """Возвращает (страница job-ов, всего под фильтрами)."""
    async with uow_factory() as uow:
        jobs = await uow.jobs.list(
            status=status,
            session_id=session_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        total = await uow.jobs.count(status=status, session_id=session_id, search=search)
    return jobs, total


async def job_status_counts(uow_factory: Callable[[], UnitOfWork]) -> dict[str, int]:
    async with uow_factory() as uow:
        return await uow.jobs.status_counts()


async def dlq_entries(
    broker: MessageBroker,
    stream: str,
    limit: int = 50,
) -> list[dict]:
    rows = await broker.read_dead(stream, count=limit)
    return [{"message_id": message_id, **payload} for message_id, payload in rows]


async def stream_overview(
    broker: MessageBroker,
    targets: list[tuple[str, str, str]],
) -> list[dict]:
    """targets — список (stream, group, kind)."""
    result = []
    for stream, group, kind in targets:
        stats = await broker.stream_stats(stream, group)
        stats["kind"] = kind
        result.append(stats)
    return result

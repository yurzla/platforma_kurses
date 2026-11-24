"""Интеграционные тесты JobRepository (требуют PostgreSQL).

Запуск: INTEGRATION_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses_assistant.adapters.persistence.orm import (
    ChatSessionORM,
    CourseORM,
    JobORM,
    UserORM,
)
from courses_assistant.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from courses_assistant.domain.models import JobStatus

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="INTEGRATION_DATABASE_URL не задан"),
]


async def test_jobs_list_counts_and_purge() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    marker = uuid.uuid4().hex
    user_id: int | None = None
    course_id: int | None = None
    session_id: int | None = None

    try:
        async with session_factory() as session:
            user = UserORM(email=f"jobs-it-{marker}@example.com", password_hash="x", name="IT")
            course = CourseORM(title=f"Jobs IT {marker}")
            session.add_all([user, course])
            await session.commit()
            user_id, course_id = user.id, course.id

        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            session_id = await uow.chat.add_session(user_id, course_id)
            done_job = await uow.jobs.add(session_id, "старый вопрос про python", None)
            await uow.jobs.add(session_id, "новый вопрос про asyncio", None)
            await uow.jobs.mark_done(done_job.id, "ответ", [], None)

        async with session_factory() as session:
            await session.execute(
                update(JobORM)
                .where(JobORM.id == done_job.id)
                .values(updated_at=datetime.now(UTC) - timedelta(days=30))
            )
            await session.commit()

        async with uow:
            done_items = await uow.jobs.list(status=JobStatus.DONE, session_id=session_id)
            assert [job.id for job in done_items] == [done_job.id]
            assert await uow.jobs.count(session_id=session_id) == 2
            assert await uow.jobs.count(session_id=session_id, search="asyncio") == 1
            counts = await uow.jobs.status_counts()
            assert counts.get("done", 0) >= 1
            assert counts.get("queued", 0) >= 1

            purged = await uow.jobs.purge_terminal(datetime.now(UTC) - timedelta(days=7))
            assert purged >= 1
            assert await uow.jobs.get(done_job.id) is None
    finally:
        async with session_factory() as session:
            if session_id is not None:
                await session.execute(delete(JobORM).where(JobORM.session_id == session_id))
                await session.execute(delete(ChatSessionORM).where(ChatSessionORM.id == session_id))
            if user_id is not None:
                await session.execute(delete(UserORM).where(UserORM.id == user_id))
            if course_id is not None:
                await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
            await session.commit()
        await engine.dispose()

"""Интеграционные тесты персистентности (требуют PostgreSQL).

Запуск: INTEGRATION_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
Схема должна быть применена (`alembic upgrade head`).
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses_assistant.adapters.persistence.orm import (
    ChatMessageORM,
    ChatSessionORM,
    CourseORM,
    UserORM,
)
from courses_assistant.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from courses_assistant.domain.models import ChatMessage, Role

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="INTEGRATION_DATABASE_URL не задан"),
]


async def test_session_and_history_roundtrip() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    marker = uuid.uuid4().hex
    user_id: int | None = None
    course_id: int | None = None

    try:
        async with session_factory() as session:
            user = UserORM(email=f"it-{marker}@example.com", password_hash="x", name="IT")
            course = CourseORM(title=f"IT курс {marker}")
            session.add_all([user, course])
            await session.commit()
            user_id, course_id = user.id, course.id

        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            session_id = await uow.chat.add_session(user_id, course_id)
            await uow.chat.add_message(
                ChatMessage(session_id=session_id, role=Role.USER, content="вопрос")
            )
            await uow.chat.add_message(
                ChatMessage(session_id=session_id, role=Role.ASSISTANT, content="ответ")
            )

        async with uow:
            history = await uow.chat.get_history(session_id, limit=10)
            assert [m.content for m in history] == ["вопрос", "ответ"]
    finally:
        async with session_factory() as session:
            if user_id is not None:
                session_ids = select(ChatSessionORM.id).where(
                    ChatSessionORM.user_id == user_id
                )
                await session.execute(
                    delete(ChatMessageORM).where(ChatMessageORM.session_id.in_(session_ids))
                )
                await session.execute(
                    delete(ChatSessionORM).where(ChatSessionORM.user_id == user_id)
                )
                await session.execute(delete(UserORM).where(UserORM.id == user_id))
            if course_id is not None:
                await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
            await session.commit()
        await engine.dispose()

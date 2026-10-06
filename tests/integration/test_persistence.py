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
    LessonORM,
    SectionORM,
    StepORM,
    UserORM,
)
from courses_assistant.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from courses_assistant.domain.models import ChatMessage, Role
from courses_assistant.scripts.renumber_steps import renumber_step_positions

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


async def test_renumber_step_positions_per_lesson() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    marker = uuid.uuid4().hex
    course_id: int | None = None

    try:
        async with session_factory() as session:
            course = CourseORM(title=f"Renumber {marker}")
            session.add(course)
            await session.flush()
            section = SectionORM(course_id=course.id, position=1, title="Модуль")
            session.add(section)
            await session.flush()
            lesson = LessonORM(section_id=section.id, title="Урок", position=1)
            session.add(lesson)
            await session.flush()
            for position in (5, 7, 9):
                session.add(
                    StepORM(
                        lesson_id=lesson.id,
                        position=position,
                        step_type="text",
                        is_enabled=True,
                    )
                )
            await session.commit()
            course_id = course.id

        async with engine.begin() as conn:
            changed = await renumber_step_positions(conn, course_id=course_id)
            assert changed == 3

        async with session_factory() as session:
            positions = (
                (
                    await session.execute(
                        select(StepORM.position)
                        .join(LessonORM, StepORM.lesson_id == LessonORM.id)
                        .join(SectionORM, LessonORM.section_id == SectionORM.id)
                        .where(SectionORM.course_id == course_id)
                        .order_by(StepORM.position)
                    )
                )
                .scalars()
                .all()
            )
            assert list(positions) == [1, 2, 3]
    finally:
        async with session_factory() as session:
            if course_id is not None:
                step_ids = select(StepORM.id).join(
                    LessonORM, StepORM.lesson_id == LessonORM.id
                ).join(SectionORM, LessonORM.section_id == SectionORM.id).where(
                    SectionORM.course_id == course_id
                )
                await session.execute(delete(StepORM).where(StepORM.id.in_(step_ids)))
                await session.execute(
                    delete(LessonORM).where(
                        LessonORM.section_id.in_(
                            select(SectionORM.id).where(SectionORM.course_id == course_id)
                        )
                    )
                )
                await session.execute(
                    delete(SectionORM).where(SectionORM.course_id == course_id)
                )
                await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
                await session.commit()
        await engine.dispose()

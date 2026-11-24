"""Интеграционные тесты управления шагами преподавателем (нужен PostgreSQL).

Запуск: INTEGRATION_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
Схема должна быть применена (`alembic upgrade head`).
"""

from __future__ import annotations

import os
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses_assistant.adapters.persistence.orm import (
    ChoiceQuestionMetadataORM,
    CourseORM,
    LessonORM,
    SectionORM,
    StepChoiceOptionORM,
    StepContentORM,
    StepORM,
    StepSourceORM,
    UserORM,
    UserStepProgressORM,
)
from courses_assistant.domain.models import User
from courses_assistant.entrypoints.api.routers.teacher import (
    create_step,
    delete_step,
    get_my_course,
    update_step,
)
from courses_assistant.entrypoints.api.schemas import (
    TeacherChoiceOptionCreate,
    TeacherStepCreate,
    TeacherStepUpdate,
)

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="INTEGRATION_DATABASE_URL не задан"),
]


async def test_teacher_step_editing_flow() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    container = SimpleNamespace(session_factory=session_factory)

    marker = uuid.uuid4().hex
    teacher_id: int | None = None
    other_id: int | None = None
    course_id: int | None = None
    try:
        async with session_factory() as session:
            teacher = UserORM(
                email=f"teacher-{marker}@example.com",
                password_hash="x",
                name="Учитель",
                role="teacher",
            )
            other = UserORM(
                email=f"other-{marker}@example.com",
                password_hash="x",
                name="Другой",
                role="teacher",
            )
            session.add_all([teacher, other])
            await session.flush()
            course = CourseORM(title=f"Курс {marker}", owner_id=teacher.id)
            session.add(course)
            await session.flush()
            section = SectionORM(course_id=course.id, title="Модуль", position=1)
            session.add(section)
            await session.flush()
            lesson = LessonORM(section_id=section.id, title="Урок", position=1)
            session.add(lesson)
            await session.commit()
            teacher_id, other_id = teacher.id, other.id
            course_id, lesson_id = course.id, lesson.id

        teacher_user = User(id=teacher_id, email="t@example.com", name="Учитель", role="teacher")
        other_user = User(id=other_id, email="o@example.com", name="Другой", role="teacher")

        created = await create_step(
            lesson_id,
            TeacherStepCreate(
                body="<p>Теория</p>",
                step_type="text",
                video_url="https://youtu.be/abc123",
            ),
            teacher_user,
            container,  # type: ignore[arg-type]
        )

        detail = await get_my_course(course_id, teacher_user, container)  # type: ignore[arg-type]
        step = detail.sections[0].lessons[0].steps[0]
        assert step.id == created.id
        assert step.body == "<p>Теория</p>"
        assert step.video_url == "https://youtu.be/abc123"

        await update_step(
            created.id,
            TeacherStepUpdate(
                step_type="choice",
                body="Вопрос",
                choices=[
                    TeacherChoiceOptionCreate(text="A", is_correct=True),
                    TeacherChoiceOptionCreate(text="B", is_correct=False),
                ],
                is_multiple_choice=False,
                video_url="https://vk.com/video-1_2",
            ),
            teacher_user,
            container,  # type: ignore[arg-type]
        )

        async with session_factory() as session:
            stored = await session.get(StepORM, created.id)
            assert stored is not None
            assert stored.step_type == "choice"
            assert stored.video_url == "https://vk.com/video-1_2"
            contents = (
                await session.execute(
                    select(StepContentORM).where(StepContentORM.step_id == created.id)
                )
            ).scalars().all()
            assert [content.body for content in contents] == ["Вопрос"]
            options = (
                await session.execute(
                    select(StepChoiceOptionORM)
                    .where(StepChoiceOptionORM.step_id == created.id)
                    .order_by(StepChoiceOptionORM.position)
                )
            ).scalars().all()
            assert [(option.option_html, option.is_correct) for option in options] == [
                ("A", True),
                ("B", False),
            ]
            assert await session.get(ChoiceQuestionMetadataORM, created.id) is not None

        await update_step(
            created.id,
            TeacherStepUpdate(step_type="string", body="Введите ответ", correct_answer="42"),
            teacher_user,
            container,  # type: ignore[arg-type]
        )

        async with session_factory() as session:
            stored = await session.get(StepORM, created.id)
            assert stored is not None
            assert stored.step_type == "string"
            options = (
                await session.execute(
                    select(StepChoiceOptionORM).where(StepChoiceOptionORM.step_id == created.id)
                )
            ).scalars().all()
            assert options == []
            source = (
                await session.execute(
                    select(StepSourceORM).where(StepSourceORM.step_id == created.id)
                )
            ).scalar_one()
            assert source.payload == {"correct": "42"}

        with pytest.raises(HTTPException) as denied:
            await update_step(
                created.id,
                TeacherStepUpdate(body="Чужое"),
                other_user,
                container,  # type: ignore[arg-type]
            )
        assert denied.value.status_code == 404

        # Три шага, удаляем средний — оставшиеся перенумеровываются.
        for body in ("Первый", "Второй"):
            await create_step(
                lesson_id,
                TeacherStepCreate(body=body),
                teacher_user,
                container,  # type: ignore[arg-type]
            )

        async with session_factory() as session:
            positions = (
                await session.execute(
                    select(StepORM.id, StepORM.position)
                    .where(StepORM.lesson_id == lesson_id)
                    .order_by(StepORM.position)
                )
            ).all()
        middle_id = positions[1][0]

        await delete_step(middle_id, teacher_user, container)  # type: ignore[arg-type]

        async with session_factory() as session:
            remaining = (
                await session.execute(
                    select(StepORM.id, StepORM.position)
                    .where(StepORM.lesson_id == lesson_id)
                    .order_by(StepORM.position)
                )
            ).all()
            assert [position for _id, position in remaining] == [1, 2]
            assert middle_id not in {step_id for step_id, _position in remaining}
    finally:
        if teacher_id is not None:
            async with session_factory() as session:
                lesson_ids = (
                    select(LessonORM.id)
                    .join(SectionORM, LessonORM.section_id == SectionORM.id)
                    .where(SectionORM.course_id == course_id)
                    if course_id is not None
                    else select(LessonORM.id).where(False)
                )
                step_ids = select(StepORM.id).where(StepORM.lesson_id.in_(lesson_ids))
                await session.execute(
                    delete(UserStepProgressORM).where(UserStepProgressORM.step_id.in_(step_ids))
                )
                await session.execute(
                    delete(StepChoiceOptionORM).where(StepChoiceOptionORM.step_id.in_(step_ids))
                )
                await session.execute(
                    delete(ChoiceQuestionMetadataORM).where(
                        ChoiceQuestionMetadataORM.step_id.in_(step_ids)
                    )
                )
                await session.execute(
                    delete(StepSourceORM).where(StepSourceORM.step_id.in_(step_ids))
                )
                await session.execute(
                    delete(StepContentORM).where(StepContentORM.step_id.in_(step_ids))
                )
                await session.execute(delete(StepORM).where(StepORM.lesson_id.in_(lesson_ids)))
                await session.execute(delete(LessonORM).where(LessonORM.id.in_(lesson_ids)))
                if course_id is not None:
                    await session.execute(
                        delete(SectionORM).where(SectionORM.course_id == course_id)
                    )
                    await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
                await session.execute(delete(UserORM).where(UserORM.id.in_([teacher_id, other_id])))
                await session.commit()
        await engine.dispose()

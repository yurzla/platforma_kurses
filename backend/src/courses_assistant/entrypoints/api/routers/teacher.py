"""Workspace преподавателя: собственные курсы и прогресс их студентов."""

from __future__ import annotations

from dataclasses import asdict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from courses_assistant.adapters.persistence.orm import (
    ChatSessionORM,
    ChoiceQuestionMetadataORM,
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
    EnrollmentORM,
    LessonORM,
    SectionORM,
    StepChoiceOptionORM,
    StepContentORM,
    StepORM,
    StepSourceORM,
    UserORM,
    UserStepProgressORM,
)
from courses_assistant.container import Container
from courses_assistant.domain.models import User
from courses_assistant.entrypoints.api.dependencies import get_container, require_teacher
from courses_assistant.entrypoints.api.schemas import (
    LessonSummaryRead,
    SectionSummaryRead,
    StepSummaryRead,
    TeacherChoiceOptionCreate,
    TeacherCourseCreate,
    TeacherCourseDetailRead,
    TeacherCourseListResponse,
    TeacherCourseRead,
    TeacherCourseUpdate,
    TeacherLessonCreate,
    TeacherLessonRead,
    TeacherSectionCreate,
    TeacherSectionRead,
    TeacherStepCreate,
    TeacherStepRead,
    TeacherStepUpdate,
    TeacherStudentProgressRead,
)

router = APIRouter(prefix="/api/v1/teacher", tags=["teacher"])
logger = structlog.get_logger(__name__)


async def _enqueue_course_index(container: Container, course_id: int) -> None:
    """Запускает eventual-consistency обновление RAG-индекса после коммита."""
    try:
        await container.broker.publish(
            container.settings.stream_index,
            {"course_id": course_id},
            maxlen=container.settings.redis_stream_maxlen,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("course_index_enqueue_failed", course_id=course_id, error=str(exc))


async def _enqueue_step_index(container: Container, step_id: int) -> None:
    try:
        await container.broker.publish(
            container.settings.stream_index,
            {"kind": "step_upsert", "step_id": step_id},
            maxlen=container.settings.redis_stream_maxlen,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("step_index_enqueue_failed", step_id=step_id, error=str(exc))


async def _owned_course(session: AsyncSession, course_id: int, teacher_id: int) -> CourseORM:
    course = await session.get(CourseORM, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    if course.owner_id != teacher_id:
        raise HTTPException(status_code=403, detail="Можно управлять только своими курсами")
    return course


async def _course_read(session: AsyncSession, course: CourseORM) -> TeacherCourseRead:
    lessons_count = await session.scalar(
        select(func.count())
        .select_from(LessonORM)
        .join(SectionORM)
        .where(SectionORM.course_id == course.id)
    )
    steps_count = await session.scalar(
        select(func.count())
        .select_from(StepORM)
        .join(LessonORM)
        .join(SectionORM)
        .where(SectionORM.course_id == course.id)
    )
    students_count = await session.scalar(
        select(func.count()).select_from(EnrollmentORM).where(EnrollmentORM.course_id == course.id)
    )
    return TeacherCourseRead(
        id=course.id,
        title=course.title,
        description=course.description,
        level=course.level,
        is_published=course.is_published,
        lessons_count=int(lessons_count or 0),
        steps_count=int(steps_count or 0),
        students_count=int(students_count or 0),
    )


async def _delete_steps(session: AsyncSession, step_ids: list[int]) -> None:
    """Удаляет шаги и все связанные с ними данные без висячих FK."""
    if not step_ids:
        return
    chunk_ids = list(
        (
            await session.execute(
                select(ContentChunkORM.id).where(ContentChunkORM.step_id.in_(step_ids))
            )
        ).scalars()
    )
    if chunk_ids:
        await session.execute(
            delete(ChunkEmbeddingORM).where(ChunkEmbeddingORM.chunk_id.in_(chunk_ids))
        )
    await session.execute(delete(ContentChunkORM).where(ContentChunkORM.step_id.in_(step_ids)))
    await session.execute(
        delete(UserStepProgressORM).where(UserStepProgressORM.step_id.in_(step_ids))
    )
    await session.execute(
        delete(StepChoiceOptionORM).where(StepChoiceOptionORM.step_id.in_(step_ids))
    )
    await session.execute(
        delete(ChoiceQuestionMetadataORM).where(ChoiceQuestionMetadataORM.step_id.in_(step_ids))
    )
    await session.execute(delete(StepSourceORM).where(StepSourceORM.step_id.in_(step_ids)))
    await session.execute(delete(StepContentORM).where(StepContentORM.step_id.in_(step_ids)))
    await session.execute(delete(StepORM).where(StepORM.id.in_(step_ids)))


def _validate_step_fields(
    *,
    step_type: str,
    body: str,
    choices: list[TeacherChoiceOptionCreate],
    is_multiple_choice: bool,
    correct_answer: str | None,
    video_url: str | None,
) -> None:
    body_text = (body or "").strip()
    if not body_text and not video_url:
        raise HTTPException(status_code=422, detail="Укажите материал или ссылку на видео")
    if step_type == "video" and not video_url:
        raise HTTPException(status_code=422, detail="Для видео-шага укажите ссылку на видео")
    if step_type == "choice":
        if len(choices) < 2:
            raise HTTPException(status_code=422, detail="Для теста нужно не менее двух вариантов")
        correct_count = sum(option.is_correct for option in choices)
        if not correct_count:
            raise HTTPException(
                status_code=422, detail="Отметьте хотя бы один правильный вариант"
            )
        if not is_multiple_choice and correct_count != 1:
            raise HTTPException(
                status_code=422,
                detail="В тесте с одним выбором должен быть один правильный вариант",
            )
    elif step_type in {"string", "number"} and not (correct_answer or "").strip():
        raise HTTPException(status_code=422, detail="Укажите правильный ответ для автопроверки")


async def _replace_step_data(
    session: AsyncSession,
    step: StepORM,
    *,
    body: str,
    choices: list[TeacherChoiceOptionCreate],
    is_multiple_choice: bool,
    correct_answer: str | None,
) -> None:
    """Перезаписывает содержимое шага под его текущий тип."""
    await session.execute(
        delete(StepChoiceOptionORM).where(StepChoiceOptionORM.step_id == step.id)
    )
    await session.execute(
        delete(ChoiceQuestionMetadataORM).where(ChoiceQuestionMetadataORM.step_id == step.id)
    )
    await session.execute(delete(StepSourceORM).where(StepSourceORM.step_id == step.id))
    await session.execute(delete(StepContentORM).where(StepContentORM.step_id == step.id))
    session.add(StepContentORM(step_id=step.id, content_type="html", body=body))
    if step.step_type == "choice":
        session.add(
            ChoiceQuestionMetadataORM(
                step_id=step.id,
                source_question_html=body,
                source_file="teacher-workspace",
                needs_review=False,
                is_multiple_choice=is_multiple_choice,
            )
        )
        for position, option in enumerate(choices):
            session.add(
                StepChoiceOptionORM(
                    step_id=step.id,
                    position=position,
                    option_html=option.text,
                    is_suggested_correct=option.is_correct,
                    is_correct=option.is_correct,
                )
            )
    elif step.step_type in {"string", "number"}:
        session.add(
            StepSourceORM(
                step_id=step.id,
                source_type="teacher-workspace",
                payload={"correct": correct_answer},
            )
        )


async def _renumber_lesson_steps(session: AsyncSession, lesson_id: int) -> None:
    step_ids = list(
        (
            await session.execute(
                select(StepORM.id)
                .where(StepORM.lesson_id == lesson_id)
                .order_by(StepORM.position, StepORM.id)
            )
        ).scalars()
    )
    for position, step_id in enumerate(step_ids, start=1):
        await session.execute(
            update(StepORM).where(StepORM.id == step_id).values(position=position)
        )


async def _owned_step(session: AsyncSession, step_id: int, teacher_id: int) -> StepORM:
    step = await session.get(StepORM, step_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    lesson = await session.get(LessonORM, step.lesson_id)
    if lesson is None or lesson.section_id is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    section = await session.get(SectionORM, lesson.section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Модуль не найден")
    course = await session.get(CourseORM, section.course_id)
    if course is None or course.owner_id != teacher_id:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    return step


@router.get("/courses", response_model=TeacherCourseListResponse)
async def list_my_courses(
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> TeacherCourseListResponse:
    async with container.uow_factory() as uow:
        courses = await uow.catalog.list_authored_courses(
            teacher.id, search=search, limit=limit, offset=offset
        )
        total = await uow.catalog.count_authored_courses(teacher.id, search=search)
    return TeacherCourseListResponse(
        items=[TeacherCourseRead(**asdict(course)) for course in courses],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/courses", response_model=TeacherCourseRead, status_code=201)
async def create_course(
    payload: TeacherCourseCreate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> TeacherCourseRead:
    async with container.session_factory() as session:
        course = CourseORM(
            title=payload.title.strip(),
            description=payload.description,
            level=payload.level,
            owner_id=teacher.id,
            is_published=False,
        )
        session.add(course)
        await session.flush()
        result = await _course_read(session, course)
        await session.commit()
        await _enqueue_course_index(container, course.id)
        return result


@router.get("/courses/{course_id}", response_model=TeacherCourseDetailRead)
async def get_my_course(
    course_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> TeacherCourseDetailRead:
    async with container.session_factory() as session:
        course = await _owned_course(session, course_id, teacher.id)
        sections = (
            (
                await session.execute(
                    select(SectionORM)
                    .where(SectionORM.course_id == course.id)
                    .order_by(SectionORM.position, SectionORM.id)
                )
            )
            .scalars()
            .all()
        )
        section_ids = [section.id for section in sections]
        lessons = (
            []
            if not section_ids
            else (
                await session.execute(
                    select(LessonORM)
                    .where(LessonORM.section_id.in_(section_ids))
                    .order_by(LessonORM.position, LessonORM.id)
                )
            )
            .scalars()
            .all()
        )
        lesson_ids = [lesson.id for lesson in lessons]
        steps = (
            []
            if not lesson_ids
            else (
                await session.execute(
                    select(StepORM)
                    .where(StepORM.lesson_id.in_(lesson_ids))
                    .order_by(StepORM.position, StepORM.id)
                )
            )
            .scalars()
            .all()
        )
        step_ids = [step.id for step in steps]
        bodies: dict[int, str | None] = {}
        choices_by_step: dict[int, list[TeacherChoiceOptionCreate]] = {}
        metadata_by_step: dict[int, bool] = {}
        correct_by_step: dict[int, str | None] = {}
        if step_ids:
            contents = (
                await session.execute(
                    select(StepContentORM)
                    .where(StepContentORM.step_id.in_(step_ids))
                    .order_by(StepContentORM.id.desc())
                )
            ).scalars()
            for content in contents:
                bodies.setdefault(content.step_id, content.body)
            options = (
                await session.execute(
                    select(StepChoiceOptionORM)
                    .where(StepChoiceOptionORM.step_id.in_(step_ids))
                    .order_by(StepChoiceOptionORM.position)
                )
            ).scalars()
            for option in options:
                choices_by_step.setdefault(option.step_id, []).append(
                    TeacherChoiceOptionCreate(
                        text=option.option_html,
                        is_correct=bool(option.is_correct),
                    )
                )
            metadatas = (
                await session.execute(
                    select(ChoiceQuestionMetadataORM).where(
                        ChoiceQuestionMetadataORM.step_id.in_(step_ids)
                    )
                )
            ).scalars()
            for metadata in metadatas:
                metadata_by_step[metadata.step_id] = metadata.is_multiple_choice
            sources = (
                await session.execute(
                    select(StepSourceORM).where(StepSourceORM.step_id.in_(step_ids))
                )
            ).scalars()
            for source in sources:
                payload = source.payload or {}
                value = payload.get("correct")
                correct_by_step[source.step_id] = None if value is None else str(value)
        steps_by_lesson: dict[int, list[TeacherStepRead]] = {}
        for step in steps:
            steps_by_lesson.setdefault(step.lesson_id, []).append(
                TeacherStepRead(
                    id=step.id,
                    position=step.position,
                    step_type=step.step_type,
                    body=bodies.get(step.id),
                    video_url=step.video_url,
                    choices=choices_by_step.get(step.id, []),
                    is_multiple_choice=metadata_by_step.get(step.id, False),
                    correct_answer=correct_by_step.get(step.id),
                )
            )
        lessons_by_section: dict[int, list[TeacherLessonRead]] = {}
        for lesson in lessons:
            if lesson.section_id is not None:
                lessons_by_section.setdefault(lesson.section_id, []).append(
                    TeacherLessonRead(
                        id=lesson.id,
                        title=lesson.title,
                        position=lesson.position,
                        steps=steps_by_lesson.get(lesson.id, []),
                    )
                )
        return TeacherCourseDetailRead(
            id=course.id,
            title=course.title,
            description=course.description,
            level=course.level,
            is_published=course.is_published,
            sections=[
                TeacherSectionRead(
                    id=section.id,
                    title=section.title,
                    position=section.position,
                    lessons=lessons_by_section.get(section.id, []),
                )
                for section in sections
            ],
        )


@router.patch("/courses/{course_id}", response_model=TeacherCourseRead)
async def update_course(
    course_id: int,
    payload: TeacherCourseUpdate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> TeacherCourseRead:
    async with container.session_factory() as session:
        course = await _owned_course(session, course_id, teacher.id)
        needs_indexing = False
        if "title" in payload.model_fields_set:
            title = payload.title.strip() if payload.title else course.title
            needs_indexing = needs_indexing or title != course.title
            course.title = title
        if "description" in payload.model_fields_set:
            needs_indexing = needs_indexing or payload.description != course.description
            course.description = payload.description
        if "level" in payload.model_fields_set:
            course.level = payload.level
        if payload.is_published is True:
            step_count = await session.scalar(
                select(func.count())
                .select_from(StepORM)
                .join(LessonORM)
                .join(SectionORM)
                .where(SectionORM.course_id == course.id, StepORM.is_enabled.is_(True))
            )
            if not step_count:
                raise HTTPException(
                    status_code=422, detail="Нельзя опубликовать курс без хотя бы одного шага"
                )
        if "is_published" in payload.model_fields_set:
            course.is_published = bool(payload.is_published)
        result = await _course_read(session, course)
        await session.commit()
        if needs_indexing:
            await _enqueue_course_index(container, course.id)
        return result


@router.post("/courses/{course_id}/sections", response_model=SectionSummaryRead, status_code=201)
async def create_section(
    course_id: int,
    payload: TeacherSectionCreate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> SectionSummaryRead:
    async with container.session_factory() as session:
        await _owned_course(session, course_id, teacher.id)
        position = int(
            await session.scalar(
                select(func.coalesce(func.max(SectionORM.position), 0) + 1).where(
                    SectionORM.course_id == course_id
                )
            )
            or 1
        )
        section = SectionORM(course_id=course_id, title=payload.title.strip(), position=position)
        session.add(section)
        await session.flush()
        await session.commit()
        return SectionSummaryRead(id=section.id, title=section.title, position=section.position)


@router.post("/sections/{section_id}/lessons", response_model=LessonSummaryRead, status_code=201)
async def create_lesson(
    section_id: int,
    payload: TeacherLessonCreate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> LessonSummaryRead:
    async with container.session_factory() as session:
        section = await session.get(SectionORM, section_id)
        if section is None:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        await _owned_course(session, section.course_id, teacher.id)
        position = int(
            await session.scalar(
                select(func.coalesce(func.max(LessonORM.position), 0) + 1).where(
                    LessonORM.section_id == section_id
                )
            )
            or 1
        )
        lesson = LessonORM(section_id=section_id, title=payload.title.strip(), position=position)
        session.add(lesson)
        await session.flush()
        await session.commit()
        return LessonSummaryRead(id=lesson.id, title=lesson.title, position=lesson.position)


@router.delete("/sections/{section_id}", status_code=204)
async def delete_section(
    section_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> None:
    async with container.session_factory() as session:
        section = await session.get(SectionORM, section_id)
        if section is None:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        await _owned_course(session, section.course_id, teacher.id)
        lesson_ids = list(
            (
                await session.execute(
                    select(LessonORM.id).where(LessonORM.section_id == section_id)
                )
            ).scalars()
        )
        step_ids = (
            []
            if not lesson_ids
            else list(
                (
                    await session.execute(
                        select(StepORM.id).where(StepORM.lesson_id.in_(lesson_ids))
                    )
                ).scalars()
            )
        )
        await _delete_steps(session, step_ids)
        if lesson_ids:
            await session.execute(delete(LessonORM).where(LessonORM.id.in_(lesson_ids)))
        await session.execute(delete(SectionORM).where(SectionORM.id == section_id))
        await session.commit()


@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> None:
    async with container.session_factory() as session:
        lesson = await session.get(LessonORM, lesson_id)
        if lesson is None or lesson.section_id is None:
            raise HTTPException(status_code=404, detail="Урок не найден")
        section = await session.get(SectionORM, lesson.section_id)
        if section is None:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        await _owned_course(session, section.course_id, teacher.id)
        step_ids = list(
            (
                await session.execute(select(StepORM.id).where(StepORM.lesson_id == lesson_id))
            ).scalars()
        )
        await _delete_steps(session, step_ids)
        await session.execute(delete(LessonORM).where(LessonORM.id == lesson_id))
        await session.commit()


@router.post("/lessons/{lesson_id}/steps", response_model=StepSummaryRead, status_code=201)
async def create_step(
    lesson_id: int,
    payload: TeacherStepCreate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> StepSummaryRead:
    async with container.session_factory() as session:
        lesson = await session.get(LessonORM, lesson_id)
        if lesson is None or lesson.section_id is None:
            raise HTTPException(status_code=404, detail="Урок не найден")
        section = await session.get(SectionORM, lesson.section_id)
        if section is None:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        await _owned_course(session, section.course_id, teacher.id)
        position = int(
            await session.scalar(
                select(func.coalesce(func.max(StepORM.position), 0) + 1).where(
                    StepORM.lesson_id == lesson_id
                )
            )
            or 1
        )
        step = StepORM(
            lesson_id=lesson_id,
            position=position,
            step_type=payload.step_type,
            video_url=payload.video_url,
        )
        session.add(step)
        await session.flush()
        _validate_step_fields(
            step_type=payload.step_type,
            body=payload.body,
            choices=payload.choices,
            is_multiple_choice=payload.is_multiple_choice,
            correct_answer=payload.correct_answer,
            video_url=payload.video_url,
        )
        await _replace_step_data(
            session,
            step,
            body=payload.body,
            choices=payload.choices,
            is_multiple_choice=payload.is_multiple_choice,
            correct_answer=payload.correct_answer,
        )
        await session.commit()
        await _enqueue_step_index(container, step.id)
        return StepSummaryRead(id=step.id, position=step.position, step_type=step.step_type)


async def _step_edit_values(
    session: AsyncSession, step: StepORM
) -> tuple[str | None, list[TeacherChoiceOptionCreate], bool, str | None]:
    content = (
        await session.execute(
            select(StepContentORM)
            .where(StepContentORM.step_id == step.id)
            .order_by(StepContentORM.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    options = (
        (
            await session.execute(
                select(StepChoiceOptionORM)
                .where(StepChoiceOptionORM.step_id == step.id)
                .order_by(StepChoiceOptionORM.position)
            )
        )
        .scalars()
        .all()
    )
    metadata = await session.get(ChoiceQuestionMetadataORM, step.id)
    source = (
        await session.execute(select(StepSourceORM).where(StepSourceORM.step_id == step.id))
    ).scalar_one_or_none()
    correct: str | None = None
    if source is not None and source.payload:
        value = source.payload.get("correct")
        correct = None if value is None else str(value)
    return (
        content.body if content is not None else None,
        [
            TeacherChoiceOptionCreate(text=option.option_html, is_correct=bool(option.is_correct))
            for option in options
        ],
        bool(metadata.is_multiple_choice) if metadata is not None else False,
        correct,
    )


@router.patch("/steps/{step_id}", response_model=TeacherStepRead)
async def update_step(
    step_id: int,
    payload: TeacherStepUpdate,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> TeacherStepRead:
    async with container.session_factory() as session:
        step = await _owned_step(session, step_id, teacher.id)
        old_body, old_choices, old_multiple, old_correct = await _step_edit_values(session, step)
        step_type = payload.step_type or step.step_type
        body = payload.body if payload.body is not None else (old_body or "")
        choices = payload.choices if payload.choices is not None else old_choices
        is_multiple_choice = (
            payload.is_multiple_choice
            if payload.is_multiple_choice is not None
            else old_multiple
        )
        correct_answer = (
            payload.correct_answer
            if "correct_answer" in payload.model_fields_set
            else old_correct
        )
        video_url = (
            payload.video_url if "video_url" in payload.model_fields_set else step.video_url
        )
        _validate_step_fields(
            step_type=step_type,
            body=body,
            choices=choices,
            is_multiple_choice=is_multiple_choice,
            correct_answer=correct_answer,
            video_url=video_url,
        )
        step.step_type = step_type
        step.video_url = video_url
        await _replace_step_data(
            session,
            step,
            body=body,
            choices=choices,
            is_multiple_choice=is_multiple_choice,
            correct_answer=correct_answer,
        )
        await session.commit()
        await _enqueue_step_index(container, step.id)
        return TeacherStepRead(
            id=step.id,
            position=step.position,
            step_type=step.step_type,
            body=body,
            video_url=step.video_url,
            choices=choices if step.step_type == "choice" else [],
            is_multiple_choice=is_multiple_choice,
            correct_answer=correct_answer if step.step_type in {"string", "number"} else None,
        )


@router.delete("/steps/{step_id}", status_code=204)
async def delete_step(
    step_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> None:
    async with container.session_factory() as session:
        step = await _owned_step(session, step_id, teacher.id)
        lesson_id = step.lesson_id
        await _delete_steps(session, [step.id])
        await _renumber_lesson_steps(session, lesson_id)
        await session.commit()


@router.delete("/courses/{course_id}", status_code=204)
async def delete_draft_course(
    course_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> None:
    async with container.session_factory() as session:
        course = await _owned_course(session, course_id, teacher.id)
        if course.is_published:
            raise HTTPException(
                status_code=409, detail="Можно удалить только неопубликованный черновик"
            )
        enrollment_count = await session.scalar(
            select(func.count())
            .select_from(EnrollmentORM)
            .where(EnrollmentORM.course_id == course_id)
        )
        chat_count = await session.scalar(
            select(func.count())
            .select_from(ChatSessionORM)
            .where(ChatSessionORM.course_id == course_id)
        )
        if enrollment_count or chat_count:
            raise HTTPException(
                status_code=409, detail="Нельзя удалить черновик с активностью студентов"
            )
        section_ids = list(
            (
                await session.execute(
                    select(SectionORM.id).where(SectionORM.course_id == course_id)
                )
            ).scalars()
        )
        lesson_ids = (
            []
            if not section_ids
            else list(
                (
                    await session.execute(
                        select(LessonORM.id).where(LessonORM.section_id.in_(section_ids))
                    )
                ).scalars()
            )
        )
        step_ids = (
            []
            if not lesson_ids
            else list(
                (
                    await session.execute(
                        select(StepORM.id).where(StepORM.lesson_id.in_(lesson_ids))
                    )
                ).scalars()
            )
        )
        await _delete_steps(session, step_ids)
        if lesson_ids:
            await session.execute(delete(LessonORM).where(LessonORM.id.in_(lesson_ids)))
        if section_ids:
            await session.execute(delete(SectionORM).where(SectionORM.id.in_(section_ids)))
        await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
        await session.commit()


@router.get("/courses/{course_id}/students", response_model=list[TeacherStudentProgressRead])
async def course_students(
    course_id: int,
    teacher: User = Depends(require_teacher),
    container: Container = Depends(get_container),
) -> list[TeacherStudentProgressRead]:
    async with container.session_factory() as session:
        await _owned_course(session, course_id, teacher.id)
        rows = (
            await session.execute(
                select(EnrollmentORM, UserORM)
                .join(UserORM, UserORM.id == EnrollmentORM.user_id)
                .where(EnrollmentORM.course_id == course_id)
                .order_by(EnrollmentORM.progress_percent.desc(), UserORM.name)
            )
        ).all()
        return [
            TeacherStudentProgressRead(
                user_id=user.id,
                name=user.name,
                email=user.email,
                progress_percent=float(enrollment.progress_percent),
                status=enrollment.status,
            )
            for enrollment, user in rows
        ]

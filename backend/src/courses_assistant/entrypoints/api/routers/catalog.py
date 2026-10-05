"""Роутер каталога обучения: курсы, шаги, ответы, прогресс."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from courses_assistant.application.commands import SubmitStepAnswer
from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container, require_student
from courses_assistant.entrypoints.api.schemas import (
    AnswerRequest,
    AnswerResult,
    CourseDetailRead,
    CourseSummaryRead,
    LessonSummaryRead,
    SectionSummaryRead,
    StepRead,
    StepSummaryRead,
)

router = APIRouter(prefix="/api/v1/courses", tags=["catalog"])


@router.get("", response_model=list[CourseSummaryRead])
async def list_courses(
    user_id: int = Depends(require_student),
    container: Container = Depends(get_container),
) -> list[CourseSummaryRead]:
    async with container.uow_factory() as uow:
        courses = await uow.catalog.list_courses(user_id)
    return [CourseSummaryRead(**asdict(course)) for course in courses]


@router.get("/{course_id}", response_model=CourseDetailRead)
async def get_course(
    course_id: int,
    user_id: int = Depends(require_student),
    container: Container = Depends(get_container),
) -> CourseDetailRead:
    async with container.uow_factory() as uow:
        course = await uow.catalog.get_course(course_id, user_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return CourseDetailRead(
        id=course.id,
        title=course.title,
        description=course.description,
        sections=[
            SectionSummaryRead(
                id=section.id,
                title=section.title,
                position=section.position,
                lessons=[
                    LessonSummaryRead(
                        id=lesson.id,
                        title=lesson.title,
                        position=lesson.position,
                        steps=[
                            StepSummaryRead(
                                id=step.id,
                                position=step.position,
                                step_type=step.step_type,
                                completed=step.completed,
                            )
                            for step in lesson.steps
                        ],
                    )
                    for lesson in section.lessons
                ],
            )
            for section in course.sections
        ],
    )


@router.get("/{course_id}/steps/{step_id}", response_model=StepRead)
async def get_step(
    course_id: int,
    step_id: int,
    user_id: int = Depends(require_student),
    container: Container = Depends(get_container),
) -> StepRead:
    async with container.uow_factory() as uow:
        step = await uow.catalog.get_step(course_id, step_id, user_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    return StepRead(
        id=step.id,
        course_id=step.course_id,
        lesson_id=step.lesson_id,
        position=step.position,
        step_type=step.step_type,
        title=step.title,
        body=step.body,
        options=step.options,
        grading=step.grading,
        completed=step.completed,
        saved_answer=step.saved_answer,
        is_correct=step.is_correct,
    )


@router.post("/{course_id}/steps/{step_id}/answer", response_model=AnswerResult)
async def submit_answer(
    course_id: int,
    step_id: int,
    payload: AnswerRequest,
    user_id: int = Depends(require_student),
    container: Container = Depends(get_container),
) -> AnswerResult:
    result = await container.handlers.submit_step_answer(
        SubmitStepAnswer(
            user_id=user_id, course_id=course_id, step_id=step_id, answer=payload.answer
        )
    )
    return AnswerResult(
        is_correct=result.is_correct,
        correct_answer=result.correct_answer,
        completed=result.completed,
        progress_percent=result.progress_percent,
    )

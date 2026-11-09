"""Доменные модели каталога обучения (курсы, шаги, прогресс)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StepSummary:
    id: int
    position: int
    step_type: str
    completed: bool = False


@dataclass(slots=True)
class LessonSummary:
    id: int
    title: str
    position: int
    steps: list[StepSummary] = field(default_factory=list)


@dataclass(slots=True)
class SectionSummary:
    id: int
    title: str
    position: int
    lessons: list[LessonSummary] = field(default_factory=list)


@dataclass(slots=True)
class CourseSummary:
    id: int
    title: str
    description: str | None = None
    lessons_count: int = 0
    steps_count: int = 0
    enrolled: bool = False
    progress_percent: float | None = None


@dataclass(slots=True)
class CourseDetail:
    id: int
    title: str
    description: str | None = None
    sections: list[SectionSummary] = field(default_factory=list)


@dataclass(slots=True)
class TeacherCourseSummary:
    id: int
    title: str
    description: str | None = None
    level: str | None = None
    is_published: bool = False
    lessons_count: int = 0
    steps_count: int = 0
    students_count: int = 0


@dataclass(slots=True)
class StepResult:
    is_correct: bool | None
    correct_answer: Any | None
    completed: bool
    progress_percent: float | None


@dataclass(slots=True)
class StepDetail:
    id: int
    course_id: int
    lesson_id: int
    position: int
    step_type: str
    title: str | None
    body: str | None
    options: dict[str, Any] | None
    grading: str
    completed: bool
    saved_answer: Any | None
    is_correct: bool | None

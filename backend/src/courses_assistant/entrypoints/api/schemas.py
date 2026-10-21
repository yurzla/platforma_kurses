"""Pydantic-схемы HTTP API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SessionCreate(BaseModel):
    course_id: int | None = Field(default=None, gt=0)


class SessionRead(BaseModel):
    id: int
    user_id: int
    course_id: int | None


class SessionListItemRead(BaseModel):
    id: int
    course_id: int | None
    course_title: str | None = None
    started_at: datetime
    last_message: str | None = None


class MessageRead(BaseModel):
    id: int | None
    role: str
    content: str
    sources: list | None = None
    used_chunk_ids: list | None = None
    created_at: datetime | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)


class JobAccepted(BaseModel):
    job_id: str
    status: str = "queued"


class JobRead(BaseModel):
    id: str
    session_id: int
    status: str
    question: str
    answer: str | None = None
    sources: list = Field(default_factory=list)
    rewritten_question: str | None = None
    error: str | None = None
    attempts: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HealthRead(BaseModel):
    status: str
    dependencies: dict[str, str] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=400)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=6, max_length=400)
    role: str = Field(default="student", max_length=20)


class MeRead(BaseModel):
    role: str | None = None
    id: int | None = None
    name: str | None = None
    email: str | None = None


class UserListItem(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime | None = None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    limit: int
    offset: int


class UserRoleUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=20)


class AdminCourseListItem(BaseModel):
    id: int
    title: str
    is_published: bool
    owner_id: int | None = None
    owner_name: str | None = None
    lessons_count: int = 0
    steps_count: int = 0
    students_count: int = 0


class AdminCourseListResponse(BaseModel):
    items: list[AdminCourseListItem]
    total: int
    limit: int
    offset: int


class AdminCourseUpdate(BaseModel):
    is_published: bool | None = None
    owner_id: int | None = Field(default=None, gt=0)


class CourseSummaryRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    lessons_count: int = 0
    steps_count: int = 0
    enrolled: bool = False
    progress_percent: float | None = None


class CourseListResponse(BaseModel):
    items: list[CourseSummaryRead]
    total: int
    limit: int
    offset: int


class StepSummaryRead(BaseModel):
    id: int
    position: int
    step_type: str
    completed: bool = False


class LessonSummaryRead(BaseModel):
    id: int
    title: str
    position: int
    steps: list[StepSummaryRead] = Field(default_factory=list)


class SectionSummaryRead(BaseModel):
    id: int
    title: str
    position: int
    lessons: list[LessonSummaryRead] = Field(default_factory=list)


class CourseDetailRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    sections: list[SectionSummaryRead] = Field(default_factory=list)


class TeacherCourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10_000)
    level: str | None = Field(default=None, max_length=50)


class TeacherCourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10_000)
    level: str | None = Field(default=None, max_length=50)
    is_published: bool | None = None


class TeacherSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class TeacherLessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class TeacherChoiceOptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5_000)
    is_correct: bool = False


class TeacherStepCreate(BaseModel):
    body: str = Field(min_length=1, max_length=100_000)
    step_type: Literal["text", "free_answer", "choice", "string", "number"] = "text"
    choices: list[TeacherChoiceOptionCreate] = Field(default_factory=list, max_length=20)
    is_multiple_choice: bool = False
    correct_answer: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def validate_grading_data(self) -> "TeacherStepCreate":
        if self.step_type == "choice":
            if len(self.choices) < 2:
                raise ValueError("Для теста нужно не менее двух вариантов")
            correct_count = sum(option.is_correct for option in self.choices)
            if not correct_count:
                raise ValueError("Отметьте хотя бы один правильный вариант")
            if not self.is_multiple_choice and correct_count != 1:
                raise ValueError("В тесте с одним выбором должен быть один правильный вариант")
        elif self.step_type in {"string", "number"} and not (self.correct_answer or "").strip():
            raise ValueError("Укажите правильный ответ для автопроверки")
        return self


class TeacherCourseRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    level: str | None = None
    is_published: bool
    lessons_count: int = 0
    steps_count: int = 0
    students_count: int = 0


class TeacherStudentProgressRead(BaseModel):
    user_id: int
    name: str
    email: str
    progress_percent: float
    status: str


class StepRead(BaseModel):
    id: int
    course_id: int
    lesson_id: int
    position: int
    step_type: str
    title: str | None = None
    body: str | None = None
    options: dict[str, Any] | None = None
    grading: str
    completed: bool = False
    saved_answer: Any | None = None
    is_correct: bool | None = None


class AnswerRequest(BaseModel):
    answer: Any | None = None


class AnswerResult(BaseModel):
    is_correct: bool | None = None
    correct_answer: Any | None = None
    completed: bool = False
    progress_percent: float | None = None


class JobListItem(BaseModel):
    id: str
    session_id: int
    status: str
    question: str
    attempts: int
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobListResponse(BaseModel):
    items: list[JobListItem]
    total: int
    limit: int
    offset: int


class DlqEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    message_id: str
    task: str | None = None
    job_id: str | None = None
    session_id: int | None = None
    error: str | None = None
    source_stream: str | None = None


class StreamStat(BaseModel):
    stream: str
    group: str
    length: int
    pending: int | None = None
    lag: int | None = None
    consumers: int | None = None


class OverviewResponse(BaseModel):
    status_counts: dict[str, int]
    streams: list[StreamStat]

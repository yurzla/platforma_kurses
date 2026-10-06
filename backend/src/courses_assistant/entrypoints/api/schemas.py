"""Pydantic-схемы HTTP API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    course_id: int = Field(gt=0)


class SessionRead(BaseModel):
    id: int
    user_id: int
    course_id: int | None


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

"""Pydantic-схемы HTTP API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from courses_assistant.domain.video import parse_video_url


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


class LearningPreferencesRead(BaseModel):
    interests: str | None = None
    goals: str | None = None
    preferred_level: Literal["beginner", "intermediate", "advanced"] | None = None


class LearningPreferencesUpdate(LearningPreferencesRead):
    interests: str | None = Field(default=None, max_length=2_000)
    goals: str | None = Field(default=None, max_length=2_000)


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


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=6, max_length=400)
    role: str = Field(default="student", min_length=1, max_length=20)


class AdminUserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=320)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=6, max_length=400)
    role: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def has_changes(self) -> AdminUserUpdate:
        if not self.model_fields_set:
            raise ValueError("Не указаны данные для изменения")
        return self


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
    body: str = Field(default="", max_length=100_000)
    step_type: Literal["text", "video", "free_answer", "choice", "string", "number"] = "text"
    choices: list[TeacherChoiceOptionCreate] = Field(default_factory=list, max_length=20)
    is_multiple_choice: bool = False
    correct_answer: str | None = Field(default=None, max_length=5_000)
    video_url: str | None = Field(default=None, max_length=2_000)

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        if parse_video_url(value) is None:
            raise ValueError("Некорректная ссылка на видео")
        return value.strip()

    @model_validator(mode="after")
    def validate_grading_data(self) -> TeacherStepCreate:
        if not self.body.strip() and not self.video_url:
            raise ValueError("Укажите материал или ссылку на видео")
        if self.step_type == "video" and not self.video_url:
            raise ValueError("Для видео-шага укажите ссылку на видео")
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


class TeacherStepUpdate(BaseModel):
    step_type: Literal["text", "video", "free_answer", "choice", "string", "number"] | None = None
    body: str | None = Field(default=None, max_length=100_000)
    choices: list[TeacherChoiceOptionCreate] | None = Field(default=None, max_length=20)
    is_multiple_choice: bool | None = None
    correct_answer: str | None = Field(default=None, max_length=5_000)
    video_url: str | None = Field(default=None, max_length=2_000)

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        if parse_video_url(value) is None:
            raise ValueError("Некорректная ссылка на видео")
        return value.strip()


class TeacherStepRead(BaseModel):
    id: int
    position: int
    step_type: str
    body: str | None = None
    video_url: str | None = None
    choices: list[TeacherChoiceOptionCreate] = Field(default_factory=list)
    is_multiple_choice: bool = False
    correct_answer: str | None = None


class TeacherLessonRead(BaseModel):
    id: int
    title: str
    position: int
    steps: list[TeacherStepRead] = Field(default_factory=list)


class TeacherSectionRead(BaseModel):
    id: int
    title: str
    position: int
    lessons: list[TeacherLessonRead] = Field(default_factory=list)


class TeacherCourseDetailRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    level: str | None = None
    is_published: bool = False
    sections: list[TeacherSectionRead] = Field(default_factory=list)


class TeacherCourseRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    level: str | None = None
    is_published: bool
    lessons_count: int = 0
    steps_count: int = 0
    students_count: int = 0


class TeacherCourseListResponse(BaseModel):
    items: list[TeacherCourseRead]
    total: int
    limit: int
    offset: int


class TeacherStudentProgressRead(BaseModel):
    user_id: int
    name: str
    email: str
    progress_percent: float
    status: str


class VideoEmbedRead(BaseModel):
    kind: Literal["iframe", "file", "link"]
    src: str


class StepRead(BaseModel):
    id: int
    course_id: int
    lesson_id: int
    position: int
    step_type: str
    title: str | None = None
    body: str | None = None
    video_url: str | None = None
    video: VideoEmbedRead | None = None
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


class ChunkListItem(BaseModel):
    id: int
    course_id: int | None = None
    course_title: str | None = None
    lesson_id: int | None = None
    lesson_title: str | None = None
    step_id: int | None = None
    chunk_index: int = 0
    source_type: str
    preview: str
    has_embedding: bool = False
    model_name: str | None = None
    created_at: datetime | None = None


class ChunkListResponse(BaseModel):
    items: list[ChunkListItem]
    total: int
    limit: int
    offset: int


class ChunkDetail(ChunkListItem):
    chunk_text: str
    embedding_dimension: int | None = None
    embedding_created_at: datetime | None = None


class IndexCourseSummary(BaseModel):
    id: int
    title: str
    chunks: int = 0
    description_chunks: int = 0
    step_chunks: int = 0
    embeddings: int = 0
    without_embedding: int = 0
    status: str = "ok"


class IndexSummary(BaseModel):
    total_chunks: int = 0
    total_embeddings: int = 0
    chunks_without_embedding: int = 0
    courses_without_embeddings: int = 0
    courses_without_chunks: int = 0
    by_source_type: dict[str, int] = Field(default_factory=dict)
    model_name: str | None = None
    dimension: int | None = None
    last_embedding_at: datetime | None = None
    courses: list[IndexCourseSummary] = Field(default_factory=list)


class JobTimeline(BaseModel):
    last_done_at: datetime | None = None
    last_failed_at: datetime | None = None
    oldest_queued_at: datetime | None = None


class RetrievalSettings(BaseModel):
    embedding_model: str
    embedding_dimension: int
    retrieval_top_k: int


class AdminHealth(BaseModel):
    status: str
    dependencies: dict[str, str] = Field(default_factory=dict)
    ollama_model: str
    ollama_model_available: bool = False
    jobs: JobTimeline = Field(default_factory=JobTimeline)
    settings: RetrievalSettings

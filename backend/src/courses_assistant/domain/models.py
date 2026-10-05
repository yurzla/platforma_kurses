"""Доменные модели, value objects и события."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UserRole(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


USER_ROLES: tuple[str, ...] = (UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
SELF_REGISTER_ROLES: tuple[str, ...] = (UserRole.STUDENT, UserRole.TEACHER)


def is_admin(role: str) -> bool:
    return role == UserRole.ADMIN


class SourceType(StrEnum):
    THEORY = "theory"
    TASK = "task"
    COURSE_DESCRIPTION = "course_description"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass(slots=True, frozen=True)
class LLMMessage:
    role: Role
    content: str


@dataclass(slots=True)
class User:
    id: int
    email: str
    name: str
    role: str


@dataclass(slots=True)
class RefreshToken:
    id: int
    user_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ChatSession:
    id: int
    user_id: int
    course_id: int | None
    started_at: datetime


@dataclass(slots=True)
class ChatMessage:
    session_id: int
    role: Role
    content: str
    id: int | None = None
    sources: list[dict] | None = None
    used_chunk_ids: list[int] | None = None
    created_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class RetrievedChunk:
    chunk_id: int
    text: str
    source_type: str
    lesson: str | None
    distance: float


@dataclass(slots=True)
class Answer:
    text: str
    sources: list[RetrievedChunk] = field(default_factory=list)
    rewritten_question: str | None = None


@dataclass(slots=True)
class QuestionJob:
    id: str
    session_id: int
    question: str
    status: JobStatus = JobStatus.QUEUED
    answer: str | None = None
    sources: list[dict] = field(default_factory=list)
    rewritten_question: str | None = None
    error: str | None = None
    attempts: int = 0
    message_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

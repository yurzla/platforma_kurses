"""Pydantic-схемы HTTP API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: int = Field(gt=0)
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

"""SQLAlchemy ORM-модели, повторяющие существующую схему edu_platform_kurses + jobs."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default="student")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserLearningPreferencesORM(Base):
    __tablename__ = "user_learning_preferences"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), primary_key=True
    )
    interests: Mapped[str | None] = mapped_column(Text)
    goals: Mapped[str | None] = mapped_column(Text)
    preferred_level: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserCourseWishlistORM(Base):
    __tablename__ = "user_course_wishlist"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), primary_key=True
    )
    course_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("courses.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CourseORM(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text, server_default="ru")
    level: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SectionORM(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    course_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("courses.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    title: Mapped[str] = mapped_column(Text, nullable=False)


class LessonORM(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    section_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("sections.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(
        "position", Integer, nullable=False, server_default="0"
    )


class StepORM(Base):
    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    lesson_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lessons.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    step_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )


class StepContentORM(Base):
    __tablename__ = "step_contents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    step_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("steps.id"), nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="html")
    body: Mapped[str | None] = mapped_column(Text)
    options: Mapped[dict | None] = mapped_column(JSONB)


class StepSourceORM(Base):
    __tablename__ = "step_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    step_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("steps.id"), nullable=False, unique=True
    )
    source_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="step-source"
    )
    payload: Mapped[dict | None] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ContentChunkORM(Base):
    __tablename__ = "content_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("courses.id"))
    lesson_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("lessons.id"))
    step_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("steps.id"))
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    source_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="theory")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChunkEmbeddingORM(Base):
    __tablename__ = "chunk_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("content_chunks.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="nomic-embed-text"
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChatSessionORM(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("courses.id"))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    used_chunk_ids: Mapped[list | None] = mapped_column(JSONB)


class EnrollmentORM(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("courses.id"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    progress_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0"
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="in_progress")


class UserStepProgressORM(Base):
    __tablename__ = "user_step_progress"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    step_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("steps.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="not_started")
    best_score: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, server_default="0"
    )
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobORM(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="queued")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[list | None] = mapped_column(JSONB)
    rewritten_question: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    message_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

"""Реализации репозиториев на SQLAlchemy async."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from courses_assistant.adapters.persistence.orm import (
    ChatMessageORM,
    ChatSessionORM,
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
    JobORM,
    LessonORM,
    UserORM,
)
from courses_assistant.application.ports import (
    ChatRepository,
    CourseChunkRepository,
    JobRepository,
)
from courses_assistant.domain.models import (
    ChatMessage,
    ChatSession,
    JobStatus,
    QuestionJob,
    RetrievedChunk,
    Role,
)


def _to_session(orm: ChatSessionORM) -> ChatSession:
    return ChatSession(
        id=orm.id,
        user_id=orm.user_id,
        course_id=orm.course_id,
        started_at=orm.started_at,
    )


def _to_message(orm: ChatMessageORM) -> ChatMessage:
    return ChatMessage(
        id=orm.id,
        session_id=orm.session_id,
        role=Role(orm.role),
        content=orm.content,
        sources=orm.sources,
        used_chunk_ids=orm.used_chunk_ids,
        created_at=orm.created_at,
    )


def _to_job(orm: JobORM) -> QuestionJob:
    return QuestionJob(
        id=orm.id,
        session_id=orm.session_id,
        question=orm.question,
        status=JobStatus(orm.status),
        answer=orm.answer,
        sources=list(orm.sources or []),
        rewritten_question=orm.rewritten_question,
        error=orm.error,
        attempts=orm.attempts,
        message_id=orm.message_id,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


class SqlChatRepository(ChatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_session(self, user_id: int, course_id: int) -> int:
        orm = ChatSessionORM(user_id=user_id, course_id=course_id)
        self._session.add(orm)
        await self._session.flush()
        return orm.id

    async def get_session(self, session_id: int) -> ChatSession | None:
        orm = await self._session.get(ChatSessionORM, session_id)
        return _to_session(orm) if orm else None

    async def add_message(self, message: ChatMessage) -> int:
        orm = ChatMessageORM(
            session_id=message.session_id,
            role=str(message.role),
            content=message.content,
            sources=message.sources,
            used_chunk_ids=message.used_chunk_ids,
        )
        self._session.add(orm)
        await self._session.flush()
        return orm.id

    async def get_history(self, session_id: int, limit: int = 10) -> list[ChatMessage]:
        result = await self._session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.desc(), ChatMessageORM.id.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return [_to_message(row) for row in rows]

    async def user_exists(self, user_id: int) -> bool:
        result = await self._session.execute(
            select(UserORM.id).where(UserORM.id == user_id)
        )
        return result.first() is not None

    async def course_exists(self, course_id: int) -> bool:
        result = await self._session.execute(
            select(CourseORM.id).where(CourseORM.id == course_id)
        )
        return result.first() is not None


class SqlCourseChunkRepository(CourseChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        course_id: int,
        embedding: Sequence[float],
        model_name: str,
        limit: int,
    ) -> list[RetrievedChunk]:
        distance = ChunkEmbeddingORM.embedding.cosine_distance(list(embedding)).label("distance")
        stmt = (
            select(
                ContentChunkORM.id,
                ContentChunkORM.chunk_text,
                ContentChunkORM.source_type,
                LessonORM.title,
                distance,
            )
            .join(ContentChunkORM, ContentChunkORM.id == ChunkEmbeddingORM.chunk_id)
            .outerjoin(LessonORM, LessonORM.id == ContentChunkORM.lesson_id)
            .where(
                ContentChunkORM.course_id == course_id,
                ChunkEmbeddingORM.model_name == model_name,
                ContentChunkORM.source_type.in_(["theory", "task"]),
            )
            .order_by(distance)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            RetrievedChunk(
                chunk_id=row[0],
                text=row[1],
                source_type=row[2],
                lesson=row[3],
                distance=float(row[4]),
            )
            for row in result.all()
        ]


class SqlJobRepository(JobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session_id: int, question: str, message_id: str | None) -> QuestionJob:
        orm = JobORM(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question=question,
            status=JobStatus.QUEUED.value,
            message_id=message_id,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return _to_job(orm)

    async def get(self, job_id: str) -> QuestionJob | None:
        orm = await self._session.get(JobORM, job_id)
        return _to_job(orm) if orm else None

    async def set_message_id(self, job_id: str, message_id: str) -> None:
        await self._session.execute(
            update(JobORM).where(JobORM.id == job_id).values(message_id=message_id)
        )

    async def mark_running(self, job_id: str) -> bool:
        result = await self._session.execute(
            update(JobORM)
            .where(JobORM.id == job_id, JobORM.status == JobStatus.QUEUED.value)
            .values(status=JobStatus.RUNNING.value)
        )
        return (getattr(result, "rowcount", 0) or 0) > 0

    async def increment_attempts(self, job_id: str) -> int:
        result = await self._session.execute(
            update(JobORM)
            .where(JobORM.id == job_id)
            .values(attempts=JobORM.attempts + 1)
            .returning(JobORM.attempts)
        )
        return int(result.scalar_one())

    async def mark_done(
        self,
        job_id: str,
        answer: str,
        sources: list[dict],
        rewritten_question: str | None,
    ) -> None:
        await self._session.execute(
            update(JobORM)
            .where(JobORM.id == job_id)
            .values(
                status=JobStatus.DONE.value,
                answer=answer,
                sources=sources,
                rewritten_question=rewritten_question,
                error=None,
            )
        )

    async def mark_failed(self, job_id: str, error: str) -> None:
        await self._session.execute(
            update(JobORM)
            .where(JobORM.id == job_id)
            .values(status=JobStatus.FAILED.value, error=error)
        )

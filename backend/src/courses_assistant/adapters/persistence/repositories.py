"""Реализации репозиториев на SQLAlchemy async."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from courses_assistant.adapters.persistence.orm import (
    ChatMessageORM,
    ChatSessionORM,
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
    EnrollmentORM,
    JobORM,
    LessonORM,
    SectionORM,
    StepContentORM,
    StepORM,
    StepSourceORM,
    UserORM,
    UserStepProgressORM,
)
from courses_assistant.application.ports import (
    CatalogRepository,
    ChatRepository,
    CourseChunkRepository,
    JobRepository,
    UserRepository,
)
from courses_assistant.domain.catalog import (
    CourseDetail,
    CourseSummary,
    LessonSummary,
    SectionSummary,
    StepDetail,
    StepSummary,
)
from courses_assistant.domain.models import (
    ChatMessage,
    ChatSession,
    JobStatus,
    QuestionJob,
    RetrievedChunk,
    Role,
    User,
)
from courses_assistant.domain.quiz import build_answer_key, grading_mode


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


def _to_user(orm: UserORM) -> User:
    return User(id=orm.id, email=orm.email, name=orm.name, role=orm.role)


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        orm = await self._session.get(UserORM, user_id)
        return _to_user(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserORM).where(func.lower(UserORM.email) == email.lower())
        )
        orm = result.scalar_one_or_none()
        return _to_user(orm) if orm else None

    async def get_password_hash(self, user_id: int) -> str | None:
        result = await self._session.execute(
            select(UserORM.password_hash).where(UserORM.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, email: str, name: str, password_hash: str, role: str) -> User:
        orm = UserORM(email=email, name=name, password_hash=password_hash, role=role)
        self._session.add(orm)
        await self._session.flush()
        return _to_user(orm)


class SqlCatalogRepository(CatalogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_courses(self, user_id: int | None) -> list[CourseSummary]:
        lessons_count = (
            select(func.count())
            .select_from(LessonORM)
            .join(SectionORM, LessonORM.section_id == SectionORM.id)
            .where(SectionORM.course_id == CourseORM.id)
            .scalar_subquery()
        )
        steps_count = (
            select(func.count())
            .select_from(StepORM)
            .join(LessonORM, StepORM.lesson_id == LessonORM.id)
            .join(SectionORM, LessonORM.section_id == SectionORM.id)
            .where(SectionORM.course_id == CourseORM.id)
            .scalar_subquery()
        )
        join_condition = EnrollmentORM.course_id == CourseORM.id
        if user_id is not None:
            join_condition = join_condition & (EnrollmentORM.user_id == user_id)
        else:
            join_condition = join_condition & (EnrollmentORM.user_id == -1)
        stmt = (
            select(CourseORM, lessons_count, steps_count, EnrollmentORM.progress_percent)
            .outerjoin(EnrollmentORM, join_condition)
            .where(CourseORM.is_published.is_(True))
            .order_by(CourseORM.id)
        )
        result = await self._session.execute(stmt)
        courses: list[CourseSummary] = []
        for course, lessons_total, steps_total, progress in result.all():
            enrolled = progress is not None
            courses.append(
                CourseSummary(
                    id=course.id,
                    title=course.title,
                    description=course.description,
                    lessons_count=int(lessons_total or 0),
                    steps_count=int(steps_total or 0),
                    enrolled=enrolled,
                    progress_percent=float(progress) if progress is not None else None,
                )
            )
        return courses

    async def get_course(self, course_id: int, user_id: int | None) -> CourseDetail | None:
        course = await self._session.get(CourseORM, course_id)
        if course is None or not course.is_published:
            return None

        sections = (
            await self._session.execute(
                select(SectionORM)
                .where(SectionORM.course_id == course_id)
                .order_by(SectionORM.position, SectionORM.id)
            )
        ).scalars().all()
        section_ids = [section.id for section in sections]

        lessons_by_section: dict[int, list[LessonORM]] = {sid: [] for sid in section_ids}
        step_rows: list[StepORM] = []
        if section_ids:
            lessons = (
                await self._session.execute(
                    select(LessonORM)
                    .where(LessonORM.section_id.in_(section_ids))
                    .order_by(LessonORM.position, LessonORM.id)
                )
            ).scalars().all()
            for lesson in lessons:
                if lesson.section_id is not None:
                    lessons_by_section.setdefault(lesson.section_id, []).append(lesson)
            lesson_ids = [lesson.id for lesson in lessons]
            if lesson_ids:
                step_rows = list(
                    (
                        await self._session.execute(
                            select(StepORM)
                            .where(StepORM.lesson_id.in_(lesson_ids))
                            .order_by(StepORM.position, StepORM.id)
                        )
                    ).scalars().all()
                )

        completed: set[int] = set()
        if user_id is not None and step_rows:
            step_ids = [step.id for step in step_rows]
            progress_rows = await self._session.execute(
                select(UserStepProgressORM.step_id, UserStepProgressORM.status).where(
                    UserStepProgressORM.user_id == user_id,
                    UserStepProgressORM.step_id.in_(step_ids),
                )
            )
            completed = {
                step_id
                for step_id, status in progress_rows.all()
                if status in ("passed",)
            }

        steps_by_lesson: dict[int, list[StepSummary]] = {}
        for step in step_rows:
            steps_by_lesson.setdefault(step.lesson_id, []).append(
                StepSummary(
                    id=step.id,
                    position=step.position,
                    step_type=step.step_type,
                    completed=step.id in completed,
                )
            )

        section_models: list[SectionSummary] = []
        for section in sections:
            lesson_models = [
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    position=lesson.position,
                    steps=steps_by_lesson.get(lesson.id, []),
                )
                for lesson in lessons_by_section.get(section.id, [])
            ]
            section_models.append(
                SectionSummary(
                    id=section.id,
                    title=section.title,
                    position=section.position,
                    lessons=lesson_models,
                )
            )
        return CourseDetail(
            id=course.id,
            title=course.title,
            description=course.description,
            sections=section_models,
        )

    async def get_step(
        self, course_id: int, step_id: int, user_id: int | None
    ) -> StepDetail | None:
        row = (
            await self._session.execute(
                select(StepORM, LessonORM.section_id)
                .join(LessonORM, StepORM.lesson_id == LessonORM.id)
                .join(SectionORM, LessonORM.section_id == SectionORM.id)
                .where(StepORM.id == step_id, SectionORM.course_id == course_id)
            )
        ).first()
        if row is None:
            return None
        step: StepORM = row[0]

        content = (
            await self._session.execute(
                select(StepContentORM)
                .where(StepContentORM.step_id == step_id)
                .order_by(StepContentORM.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        source = (
            await self._session.execute(
                select(StepSourceORM).where(StepSourceORM.step_id == step_id)
            )
        ).scalar_one_or_none()
        payload = source.payload if source is not None else None

        key = build_answer_key(step.step_type, payload)
        mode = "auto" if grading_mode(step.step_type) == "auto" and key is not None else "manual"
        options: dict[str, Any] | None = None
        if mode == "auto" and step.step_type == "choice" and key is not None:
            options = {
                "choices": key["choices"],
                "is_multiple_choice": key["is_multiple_choice"],
            }

        completed = False
        if user_id is not None:
            progress = (
                await self._session.execute(
                    select(UserStepProgressORM).where(
                        UserStepProgressORM.user_id == user_id,
                        UserStepProgressORM.step_id == step_id,
                    )
                )
            ).scalar_one_or_none()
            completed = progress is not None and progress.status in ("passed",)

        return StepDetail(
            id=step.id,
            course_id=course_id,
            lesson_id=step.lesson_id,
            position=step.position,
            step_type=step.step_type,
            title=None,
            body=content.body if content is not None else None,
            options=options,
            grading=mode,
            completed=completed,
            saved_answer=None,
            is_correct=None,
        )

    async def get_answer_key(self, step_id: int) -> dict | None:
        result = await self._session.execute(
            select(StepSourceORM.payload).where(StepSourceORM.step_id == step_id)
        )
        return result.scalar_one_or_none()

    async def save_step_result(
        self,
        user_id: int,
        step_id: int,
        *,
        status: str,
        score: float,
    ) -> None:
        progress = (
            await self._session.execute(
                select(UserStepProgressORM).where(
                    UserStepProgressORM.user_id == user_id,
                    UserStepProgressORM.step_id == step_id,
                )
            )
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if progress is None:
            self._session.add(
                UserStepProgressORM(
                    user_id=user_id,
                    step_id=step_id,
                    status=status,
                    best_score=score,
                    attempts_count=1,
                    last_attempt_at=now,
                )
            )
        else:
            progress.attempts_count += 1
            progress.best_score = max(float(progress.best_score), score)
            progress.status = status
            progress.last_attempt_at = now
        await self._session.flush()

    async def recompute_course_progress(self, user_id: int, course_id: int) -> float:
        total = (
            await self._session.execute(
                select(func.count())
                .select_from(StepORM)
                .join(LessonORM, StepORM.lesson_id == LessonORM.id)
                .join(SectionORM, LessonORM.section_id == SectionORM.id)
                .where(SectionORM.course_id == course_id, StepORM.is_enabled.is_(True))
            )
        ).scalar_one()
        if not total:
            return 0.0
        done = (
            await self._session.execute(
                select(func.count())
                .select_from(UserStepProgressORM)
                .join(StepORM, UserStepProgressORM.step_id == StepORM.id)
                .join(LessonORM, StepORM.lesson_id == LessonORM.id)
                .join(SectionORM, LessonORM.section_id == SectionORM.id)
                .where(
                    SectionORM.course_id == course_id,
                    UserStepProgressORM.user_id == user_id,
                    UserStepProgressORM.status.in_(("passed",)),
                )
            )
        ).scalar_one()
        percent = round(100.0 * int(done) / int(total), 2)
        enrollment = (
            await self._session.execute(
                select(EnrollmentORM).where(
                    EnrollmentORM.user_id == user_id,
                    EnrollmentORM.course_id == course_id,
                )
            )
        ).scalar_one_or_none()
        if enrollment is None:
            self._session.add(
                EnrollmentORM(
                    user_id=user_id,
                    course_id=course_id,
                    progress_percent=percent,
                    status="completed" if percent >= 100 else "in_progress",
                )
            )
        else:
            enrollment.progress_percent = percent
            enrollment.status = "completed" if percent >= 100 else "in_progress"
        await self._session.flush()
        return percent


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

    @staticmethod
    def _filters(
        status: JobStatus | None,
        session_id: int | None,
        search: str | None,
    ) -> list:
        conditions: list = []
        if status is not None:
            conditions.append(JobORM.status == status.value)
        if session_id is not None:
            conditions.append(JobORM.session_id == session_id)
        if search:
            conditions.append(JobORM.question.ilike(f"%{search}%"))
        return conditions

    async def list(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QuestionJob]:
        stmt = select(JobORM).order_by(JobORM.created_at.desc(), JobORM.id.desc())
        conditions = self._filters(status, session_id, search)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_job(row) for row in rows]

    async def count(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(JobORM)
        conditions = self._filters(status, session_id, search)
        if conditions:
            stmt = stmt.where(*conditions)
        return int((await self._session.execute(stmt)).scalar_one())

    async def status_counts(self) -> dict[str, int]:
        result = await self._session.execute(
            select(JobORM.status, func.count()).group_by(JobORM.status)
        )
        return {str(status): int(count) for status, count in result.all()}

    async def purge_terminal(self, older_than: datetime) -> int:
        result = cast(
            "CursorResult[Any]",
            await self._session.execute(
                delete(JobORM).where(
                    JobORM.status.in_([JobStatus.DONE.value, JobStatus.FAILED.value]),
                    JobORM.updated_at < older_than,
                )
            ),
        )
        return int(result.rowcount or 0)

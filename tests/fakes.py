"""Фейковые адаптеры и in-memory UoW для тестов."""

from __future__ import annotations

import uuid
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import TracebackType

from courses_assistant.application.ports import (
    LLM,
    CatalogRepository,
    ChatRepository,
    CourseChunkRepository,
    Embedder,
    JobRepository,
    MessageBroker,
    RefreshTokenRepository,
    UnitOfWork,
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
    LLMMessage,
    QuestionJob,
    RefreshToken,
    RetrievedChunk,
    User,
)
from courses_assistant.domain.quiz import build_answer_key, grading_mode


@dataclass
class FakeStore:
    users: set[int] = field(default_factory=set)
    courses: set[int] = field(default_factory=set)
    user_profiles: dict[int, User] = field(default_factory=dict)
    user_password_hashes: dict[int, str] = field(default_factory=dict)
    sessions: dict[int, ChatSession] = field(default_factory=dict)
    messages: dict[int, list[ChatMessage]] = field(default_factory=dict)
    jobs: dict[str, QuestionJob] = field(default_factory=dict)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    courses_detail: dict[int, CourseDetail] = field(default_factory=dict)
    answer_keys: dict[int, dict] = field(default_factory=dict)
    step_bodies: dict[int, str] = field(default_factory=dict)
    progress: dict[tuple[int, int], str] = field(default_factory=dict)
    refresh_tokens: dict[str, RefreshToken] = field(default_factory=dict)
    session_seq: int = 0
    message_seq: int = 0
    user_seq: int = 0
    refresh_seq: int = 0

    def add_course(self, course: CourseDetail) -> None:
        self.courses_detail[course.id] = course

    def next_user_id(self) -> int:
        self.user_seq += 1
        return self.user_seq

    def add_user(self, email: str, name: str, password_hash: str, role: str = "student") -> User:
        user = User(id=self.next_user_id(), email=email, name=name, role=role)
        self.users.add(user.id)
        self.user_profiles[user.id] = user
        self.user_password_hashes[user.id] = password_hash
        return user

    def next_session_id(self) -> int:
        self.session_seq += 1
        return self.session_seq

    def next_message_id(self) -> int:
        self.message_seq += 1
        return self.message_seq


class InMemoryChatRepository(ChatRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    async def add_session(self, user_id: int, course_id: int) -> int:
        session_id = self._store.next_session_id()
        self._store.sessions[session_id] = ChatSession(
            id=session_id, user_id=user_id, course_id=course_id, started_at=datetime.now(UTC)
        )
        self._store.messages.setdefault(session_id, [])
        return session_id

    async def get_session(self, session_id: int) -> ChatSession | None:
        return self._store.sessions.get(session_id)

    async def add_message(self, message: ChatMessage) -> int:
        message_id = self._store.next_message_id()
        message.id = message_id
        message.created_at = datetime.now(UTC)
        self._store.messages.setdefault(message.session_id, []).append(message)
        return message_id

    async def get_history(self, session_id: int, limit: int = 10) -> list[ChatMessage]:
        return self._store.messages.get(session_id, [])[-limit:]

    async def user_exists(self, user_id: int) -> bool:
        return user_id in self._store.users

    async def course_exists(self, course_id: int) -> bool:
        return course_id in self._store.courses


class InMemoryCourseChunkRepository(CourseChunkRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    async def search(
        self,
        course_id: int,
        embedding: Sequence[float],
        model_name: str,
        limit: int,
    ) -> list[RetrievedChunk]:
        return self._store.chunks[:limit]


class InMemoryUserRepository(UserRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    async def get(self, user_id: int) -> User | None:
        return self._store.user_profiles.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        target = email.lower()
        for user in self._store.user_profiles.values():
            if user.email.lower() == target:
                return user
        return None

    async def get_password_hash(self, user_id: int) -> str | None:
        return self._store.user_password_hashes.get(user_id)

    async def create(self, email: str, name: str, password_hash: str, role: str) -> User:
        return self._store.add_user(email, name, password_hash, role)

    async def list(
        self,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        users = sorted(self._store.user_profiles.values(), key=lambda user: user.id)
        if search:
            needle = search.lower()
            users = [
                user
                for user in users
                if needle in user.email.lower() or needle in user.name.lower()
            ]
        return users[offset : offset + limit]

    async def count(self, search: str | None = None) -> int:
        users = list(self._store.user_profiles.values())
        if search:
            needle = search.lower()
            users = [
                user
                for user in users
                if needle in user.email.lower() or needle in user.name.lower()
            ]
        return len(users)

    async def set_role(self, user_id: int, role: str) -> User | None:
        user = self._store.user_profiles.get(user_id)
        if user is None:
            return None
        user.role = role
        return user


class InMemoryCatalogRepository(CatalogRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    def _all_steps(self) -> Iterator[tuple[CourseDetail, LessonSummary, StepSummary]]:
        for course in self._store.courses_detail.values():
            for section in course.sections:
                for lesson in section.lessons:
                    for step in lesson.steps:
                        yield course, lesson, step

    async def list_courses(
        self, user_id: int | None, *, enrolled_only: bool = False
    ) -> list[CourseSummary]:
        summaries: list[CourseSummary] = []
        for course in self._store.courses_detail.values():
            lessons = sum(len(section.lessons) for section in course.sections)
            course_steps = [
                step
                for section in course.sections
                for lesson in section.lessons
                for step in lesson.steps
            ]
            steps = len(course_steps)
            done = sum(
                1
                for step in course_steps
                if self._store.progress.get((user_id or 0, step.id)) in ("passed",)
            )
            percent = round(100.0 * done / steps, 2) if steps else 0.0
            enrolled = user_id is not None and any(
                (user_id, step.id) in self._store.progress for step in course_steps
            )
            if enrolled_only and not enrolled:
                continue
            summaries.append(
                CourseSummary(
                    id=course.id,
                    title=course.title,
                    description=course.description,
                    lessons_count=lessons,
                    steps_count=steps,
                    enrolled=enrolled,
                    progress_percent=percent if user_id is not None else None,
                )
            )
        return summaries

    async def get_course(self, course_id: int, user_id: int | None) -> CourseDetail | None:
        course = self._store.courses_detail.get(course_id)
        if course is None:
            return None
        sections = []
        for section in course.sections:
            lessons = []
            for lesson in section.lessons:
                steps = []
                for step in lesson.steps:
                    status = self._store.progress.get((user_id or 0, step.id))
                    steps.append(
                        StepSummary(
                            id=step.id,
                            position=step.position,
                            step_type=step.step_type,
                            completed=status in ("passed",),
                        )
                    )
                lessons.append(
                    LessonSummary(
                        id=lesson.id,
                        title=lesson.title,
                        position=lesson.position,
                        steps=steps,
                    )
                )
            sections.append(
                SectionSummary(
                    id=section.id,
                    title=section.title,
                    position=section.position,
                    lessons=lessons,
                )
            )
        return CourseDetail(
            id=course.id,
            title=course.title,
            description=course.description,
            sections=sections,
        )

    async def get_step(
        self, course_id: int, step_id: int, user_id: int | None
    ) -> StepDetail | None:
        for course, lesson, step in self._all_steps():
            if course.id != course_id or step.id != step_id:
                continue
            payload = self._store.answer_keys.get(step_id)
            key = build_answer_key(step.step_type, payload)
            mode = (
                "auto"
                if grading_mode(step.step_type) == "auto" and key is not None
                else "manual"
            )
            options = None
            if mode == "auto" and step.step_type == "choice" and key is not None:
                options = {
                    "choices": key["choices"],
                    "is_multiple_choice": key["is_multiple_choice"],
                }
            status = self._store.progress.get((user_id or 0, step_id))
            return StepDetail(
                id=step.id,
                course_id=course_id,
                lesson_id=lesson.id,
                position=step.position,
                step_type=step.step_type,
                title=None,
                body=self._store.step_bodies.get(step_id),
                options=options,
                grading=mode,
                completed=status in ("passed",),
                saved_answer=None,
                is_correct=None,
            )
        return None

    async def get_answer_key(self, step_id: int) -> dict | None:
        return self._store.answer_keys.get(step_id)

    async def save_step_result(
        self, user_id: int, step_id: int, *, status: str, score: float
    ) -> None:
        self._store.progress[(user_id, step_id)] = status

    async def recompute_course_progress(self, user_id: int, course_id: int) -> float:
        total = 0
        done = 0
        for course, _, step in self._all_steps():
            if course.id != course_id:
                continue
            total += 1
            if self._store.progress.get((user_id, step.id)) in ("passed",):
                done += 1
        return round(100.0 * done / total, 2) if total else 0.0


class InMemoryJobRepository(JobRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    async def add(self, session_id: int, question: str, message_id: str | None) -> QuestionJob:
        job = QuestionJob(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question=question,
            status=JobStatus.QUEUED,
            message_id=message_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._store.jobs[job.id] = job
        return job

    async def get(self, job_id: str) -> QuestionJob | None:
        return self._store.jobs.get(job_id)

    async def set_message_id(self, job_id: str, message_id: str) -> None:
        job = self._store.jobs.get(job_id)
        if job:
            job.message_id = message_id

    async def mark_running(self, job_id: str) -> bool:
        job = self._store.jobs.get(job_id)
        if job is None or job.status != JobStatus.QUEUED:
            return False
        job.status = JobStatus.RUNNING
        return True

    async def increment_attempts(self, job_id: str) -> int:
        job = self._store.jobs[job_id]
        job.attempts += 1
        return job.attempts

    async def mark_done(
        self,
        job_id: str,
        answer: str,
        sources: list[dict],
        rewritten_question: str | None,
    ) -> None:
        job = self._store.jobs[job_id]
        job.status = JobStatus.DONE
        job.answer = answer
        job.sources = sources
        job.rewritten_question = rewritten_question
        job.updated_at = datetime.now(UTC)

    async def mark_failed(self, job_id: str, error: str) -> None:
        job = self._store.jobs[job_id]
        job.status = JobStatus.FAILED
        job.error = error
        job.updated_at = datetime.now(UTC)

    def _filtered(
        self,
        status: JobStatus | None,
        session_id: int | None,
        search: str | None,
    ) -> list[QuestionJob]:
        jobs = list(self._store.jobs.values())
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        if session_id is not None:
            jobs = [job for job in jobs if job.session_id == session_id]
        if search:
            jobs = [job for job in jobs if search.lower() in job.question.lower()]
        return jobs

    async def list(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QuestionJob]:
        jobs = self._filtered(status, session_id, search)
        jobs.sort(key=lambda job: job.created_at or datetime.now(UTC), reverse=True)
        return jobs[offset : offset + limit]

    async def count(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
    ) -> int:
        return len(self._filtered(status, session_id, search))

    async def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for job in self._store.jobs.values():
            key = str(job.status)
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def purge_terminal(self, older_than: datetime) -> int:
        to_delete = [
            job_id
            for job_id, job in self._store.jobs.items()
            if job.status in (JobStatus.DONE, JobStatus.FAILED)
            and job.updated_at is not None
            and job.updated_at < older_than
        ]
        for job_id in to_delete:
            del self._store.jobs[job_id]
        return len(to_delete)


class InMemoryRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, store: FakeStore) -> None:
        self._store = store

    async def add(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._store.refresh_seq += 1
        self._store.refresh_tokens[token_hash] = RefreshToken(
            id=self._store.refresh_seq,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
            created_at=datetime.now(UTC),
        )

    async def get(self, token_hash: str) -> RefreshToken | None:
        return self._store.refresh_tokens.get(token_hash)

    async def revoke(self, token_hash: str, revoked_at: datetime) -> bool:
        token = self._store.refresh_tokens.get(token_hash)
        if token is None or token.revoked_at is not None:
            return False
        token.revoked_at = revoked_at
        return True

    async def revoke_all_for_user(self, user_id: int, revoked_at: datetime) -> None:
        for token in self._store.refresh_tokens.values():
            if token.user_id == user_id and token.revoked_at is None:
                token.revoked_at = revoked_at


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self, store: FakeStore) -> None:
        self._store = store
        self.chat = InMemoryChatRepository(store)
        self.chunks = InMemoryCourseChunkRepository(store)
        self.jobs = InMemoryJobRepository(store)
        self.users = InMemoryUserRepository(store)
        self.catalog = InMemoryCatalogRepository(store)
        self.refresh_tokens = InMemoryRefreshTokenRepository(store)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class FakeLLM(LLM):
    def __init__(self, responses: list[str] | None = None, default: str = "тестовый ответ") -> None:
        self._responses = list(responses or [])
        self._default = default
        self.calls: list[Sequence[LLMMessage]] = []

    async def generate(self, messages: Sequence[LLMMessage], temperature: float) -> str:
        self.calls.append(list(messages))
        if self._responses:
            return self._responses.pop(0)
        return self._default


class FakeEmbedder(Embedder):
    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension

    async def embed(self, text: str) -> list[float]:
        return [0.0] * self._dimension


class FakeBroker(MessageBroker):
    def __init__(self) -> None:
        self.published: list[tuple[str, dict]] = []
        self.acked: list[tuple[str, str, str]] = []
        self.dead: list[tuple[str, dict, str]] = []
        self.dead_entries: dict[str, list[tuple[str, dict]]] = {}

    async def publish(self, stream: str, payload: dict, maxlen: int | None = None) -> str:
        self.published.append((stream, payload))
        return f"{stream}-{len(self.published)}"

    async def ensure_group(self, stream: str, group: str) -> None:
        return None

    async def read_group(self, stream, group, consumer, count=1, block_ms=5000):  # type: ignore[no-untyped-def]
        return []

    async def reclaim_pending(self, stream, group, consumer, min_idle_ms, count=10):  # type: ignore[no-untyped-def]
        return []

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        self.acked.append((stream, group, message_id))

    async def move_to_dead(
        self,
        stream: str,
        dead_stream: str,
        payload: dict,
        reason: str,
        maxlen: int | None = None,
    ) -> None:
        self.dead.append((dead_stream, payload, reason))
        entry = {**payload, "error": reason, "source_stream": stream}
        self.dead_entries.setdefault(dead_stream, []).insert(
            0, (f"{dead_stream}-{len(self.dead)}", entry)
        )

    async def read_dead(self, stream: str, count: int = 50) -> list[tuple[str, dict]]:
        return self.dead_entries.get(stream, [])[:count]

    async def stream_stats(self, stream: str, group: str) -> dict:
        return {
            "stream": stream,
            "group": group,
            "length": len(self.dead_entries.get(stream, [])),
            "pending": 0,
            "lag": 0,
            "consumers": 1,
        }

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None

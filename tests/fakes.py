"""Фейковые адаптеры и in-memory UoW для тестов."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import TracebackType

from courses_assistant.application.ports import (
    LLM,
    ChatRepository,
    CourseChunkRepository,
    Embedder,
    JobRepository,
    MessageBroker,
    UnitOfWork,
)
from courses_assistant.domain.models import (
    ChatMessage,
    ChatSession,
    JobStatus,
    LLMMessage,
    QuestionJob,
    RetrievedChunk,
)


@dataclass
class FakeStore:
    users: set[int] = field(default_factory=set)
    courses: set[int] = field(default_factory=set)
    sessions: dict[int, ChatSession] = field(default_factory=dict)
    messages: dict[int, list[ChatMessage]] = field(default_factory=dict)
    jobs: dict[str, QuestionJob] = field(default_factory=dict)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    session_seq: int = 0
    message_seq: int = 0

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


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self, store: FakeStore) -> None:
        self._store = store
        self.chat = InMemoryChatRepository(store)
        self.chunks = InMemoryCourseChunkRepository(store)
        self.jobs = InMemoryJobRepository(store)

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

    async def publish(self, stream: str, payload: dict) -> str:
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
        self, stream: str, dead_stream: str, payload: dict, reason: str
    ) -> None:
        self.dead.append((dead_stream, payload, reason))

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None

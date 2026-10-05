"""Порты (интерфейсы) приложения. Реализации живут в adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from types import TracebackType

from courses_assistant.domain.models import (
    ChatMessage,
    ChatSession,
    LLMMessage,
    QuestionJob,
    RetrievedChunk,
)


class LLM(ABC):
    @abstractmethod
    async def generate(self, messages: Sequence[LLMMessage], temperature: float) -> str:
        """Возвращает текстовый ответ модели."""


class Embedder(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Возвращает вектор текста."""


class ChatRepository(ABC):
    @abstractmethod
    async def add_session(self, user_id: int, course_id: int) -> int: ...

    @abstractmethod
    async def get_session(self, session_id: int) -> ChatSession | None: ...

    @abstractmethod
    async def add_message(self, message: ChatMessage) -> int: ...

    @abstractmethod
    async def get_history(self, session_id: int, limit: int = 10) -> list[ChatMessage]: ...

    @abstractmethod
    async def user_exists(self, user_id: int) -> bool: ...

    @abstractmethod
    async def course_exists(self, course_id: int) -> bool: ...


class CourseChunkRepository(ABC):
    @abstractmethod
    async def search(
        self,
        course_id: int,
        embedding: Sequence[float],
        model_name: str,
        limit: int,
    ) -> list[RetrievedChunk]: ...


class JobRepository(ABC):
    @abstractmethod
    async def add(self, session_id: int, question: str, message_id: str | None) -> QuestionJob: ...

    @abstractmethod
    async def get(self, job_id: str) -> QuestionJob | None: ...

    @abstractmethod
    async def set_message_id(self, job_id: str, message_id: str) -> None: ...

    @abstractmethod
    async def mark_running(self, job_id: str) -> bool:
        """Переводит job в running. Возвращает False, если переход невозможен."""

    @abstractmethod
    async def increment_attempts(self, job_id: str) -> int:
        """Увеличивает счётчик попыток и возвращает новое значение."""

    @abstractmethod
    async def mark_done(
        self,
        job_id: str,
        answer: str,
        sources: list[dict],
        rewritten_question: str | None,
    ) -> None: ...

    @abstractmethod
    async def mark_failed(self, job_id: str, error: str) -> None: ...


class UnitOfWork(ABC):
    chat: ChatRepository
    chunks: CourseChunkRepository
    jobs: JobRepository

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


class MessageBroker(ABC):
    @abstractmethod
    async def publish(self, stream: str, payload: dict) -> str:
        """Публикует сообщение, возвращает id."""

    @abstractmethod
    async def ensure_group(self, stream: str, group: str) -> None: ...

    @abstractmethod
    async def read_group(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[tuple[str, dict]]:
        """Читает новые сообщения группы. Возвращает (message_id, payload)."""

    @abstractmethod
    async def reclaim_pending(
        self,
        stream: str,
        group: str,
        consumer: str,
        min_idle_ms: int,
        count: int = 10,
    ) -> list[tuple[str, dict]]: ...

    @abstractmethod
    async def ack(self, stream: str, group: str, message_id: str) -> None: ...

    @abstractmethod
    async def move_to_dead(
        self, stream: str, dead_stream: str, payload: dict, reason: str
    ) -> None: ...

    @abstractmethod
    async def ping(self) -> bool:
        """Проверка доступности брокера."""

    @abstractmethod
    async def close(self) -> None: ...

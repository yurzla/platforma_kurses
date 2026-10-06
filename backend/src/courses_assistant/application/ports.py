"""Порты (интерфейсы) приложения. Реализации живут в adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from types import TracebackType

from courses_assistant.domain.catalog import (
    CourseDetail,
    CourseSummary,
    StepDetail,
)
from courses_assistant.domain.models import (
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
    JobStatus,
    LLMMessage,
    QuestionJob,
    RefreshToken,
    RetrievedChunk,
    User,
)


class LLM(ABC):
    @abstractmethod
    async def generate(self, messages: Sequence[LLMMessage], temperature: float) -> str:
        """Возвращает текстовый ответ модели."""


class Embedder(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Возвращает вектор текста."""


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        """Создаёт подписанный access-токен для пользователя."""

    @abstractmethod
    def decode_access_token(self, token: str) -> int:
        """Возвращает id пользователя из токена или бросает InvalidToken."""


class ChatRepository(ABC):
    @abstractmethod
    async def add_session(self, user_id: int, course_id: int | None) -> int: ...

    @abstractmethod
    async def get_session(self, session_id: int) -> ChatSession | None: ...

    @abstractmethod
    async def list_sessions(self, user_id: int) -> list[ChatSessionSummary]: ...

    @abstractmethod
    async def add_message(self, message: ChatMessage) -> int: ...

    @abstractmethod
    async def get_history(self, session_id: int, limit: int = 10) -> list[ChatMessage]: ...

    @abstractmethod
    async def user_exists(self, user_id: int) -> bool: ...

    @abstractmethod
    async def course_exists(self, course_id: int) -> bool: ...


class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_password_hash(self, user_id: int) -> str | None: ...

    @abstractmethod
    async def create(self, email: str, name: str, password_hash: str, role: str) -> User: ...

    @abstractmethod
    async def list(
        self,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]: ...

    @abstractmethod
    async def count(self, search: str | None = None) -> int: ...

    @abstractmethod
    async def set_role(self, user_id: int, role: str) -> User | None: ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def add(self, user_id: int, token_hash: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def get(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_hash: str, revoked_at: datetime) -> bool:
        """Отзывает токен; True, если он был активен."""

    @abstractmethod
    async def revoke_all_for_user(self, user_id: int, revoked_at: datetime) -> None: ...


class CatalogRepository(ABC):
    @abstractmethod
    async def list_courses(
        self,
        user_id: int | None,
        *,
        enrolled_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CourseSummary]: ...

    @abstractmethod
    async def count_courses(
        self, user_id: int | None, *, enrolled_only: bool = False
    ) -> int: ...

    @abstractmethod
    async def get_course(self, course_id: int, user_id: int | None) -> CourseDetail | None: ...

    @abstractmethod
    async def get_step(
        self, course_id: int, step_id: int, user_id: int | None
    ) -> StepDetail | None: ...

    @abstractmethod
    async def get_answer_key(self, step_id: int) -> dict | None: ...

    @abstractmethod
    async def save_step_result(
        self,
        user_id: int,
        step_id: int,
        *,
        status: str,
        score: float,
    ) -> None: ...

    @abstractmethod
    async def recompute_course_progress(self, user_id: int, course_id: int) -> float: ...


class CourseChunkRepository(ABC):
    @abstractmethod
    async def search(
        self,
        course_id: int | None,
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

    @abstractmethod
    async def list(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QuestionJob]:
        """Список job-ов с фильтрами (для админки), новые сверху."""

    @abstractmethod
    async def count(
        self,
        status: JobStatus | None = None,
        session_id: int | None = None,
        search: str | None = None,
    ) -> int:
        """Число job-ов под те же фильтры, что и list (без пагинации)."""

    @abstractmethod
    async def status_counts(self) -> dict[str, int]:
        """Сколько job-ов в каждом статусе."""

    @abstractmethod
    async def purge_terminal(self, older_than: datetime) -> int:
        """Удаляет завершённые (done/failed) job-ы старше указанного момента."""


class UnitOfWork(ABC):
    chat: ChatRepository
    chunks: CourseChunkRepository
    jobs: JobRepository
    users: UserRepository
    catalog: CatalogRepository
    refresh_tokens: RefreshTokenRepository

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
    async def publish(self, stream: str, payload: dict, maxlen: int | None = None) -> str:
        """Публикует сообщение (опционально с approximate-trim по maxlen), возвращает id."""

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
        self,
        stream: str,
        dead_stream: str,
        payload: dict,
        reason: str,
        maxlen: int | None = None,
    ) -> None: ...

    @abstractmethod
    async def read_dead(self, stream: str, count: int = 50) -> list[tuple[str, dict]]:
        """Читает записи DLQ (новые сверху). Возвращает (message_id, payload)."""

    @abstractmethod
    async def stream_stats(self, stream: str, group: str) -> dict:
        """Возвращает метрики стрима: length, pending, lag, consumers."""

    @abstractmethod
    async def ping(self) -> bool:
        """Проверка доступности брокера."""

    @abstractmethod
    async def close(self) -> None: ...

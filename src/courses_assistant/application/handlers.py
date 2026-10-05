"""Обработчики команд приложения."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import structlog

from courses_assistant.application.commands import (
    CreateChatSession,
    ProcessQuestion,
    RunCronTask,
    SendQuestion,
)
from courses_assistant.application.ports import LLM, Embedder, MessageBroker, UnitOfWork
from courses_assistant.application.rag import generate_answer, rewrite_question
from courses_assistant.config import Settings
from courses_assistant.domain.context import build_context
from courses_assistant.domain.errors import (
    CourseNotFound,
    JobNotFound,
    SessionNotFound,
    UserNotFound,
)
from courses_assistant.domain.models import Answer, ChatMessage, JobStatus, RetrievedChunk, Role

NO_MATERIALS_ANSWER = "Не удалось найти подходящие материалы в текущем курсе."
NO_COURSE_ANSWER = "Материалы курса не найдены."

logger = structlog.get_logger(__name__)


def _chunk_to_source(chunk: RetrievedChunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "source_type": chunk.source_type,
        "lesson": chunk.lesson,
        "distance": chunk.distance,
    }


class Handlers:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        llm: LLM,
        embedder: Embedder,
        broker: MessageBroker,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._llm = llm
        self._embedder = embedder
        self._broker = broker
        self._settings = settings

    async def create_session(self, command: CreateChatSession) -> int:
        async with self._uow_factory() as uow:
            if not await uow.chat.user_exists(command.user_id):
                raise UserNotFound(f"Пользователь {command.user_id} не найден.")
            if not await uow.chat.course_exists(command.course_id):
                raise CourseNotFound(f"Курс {command.course_id} не найден.")
            session_id = await uow.chat.add_session(command.user_id, command.course_id)
        return session_id

    async def send_question(self, command: SendQuestion) -> str:
        async with self._uow_factory() as uow:
            session = await uow.chat.get_session(command.session_id)
            if session is None:
                raise SessionNotFound(f"Чат-сессия {command.session_id} не найдена.")
            job = await uow.jobs.add(command.session_id, command.question, message_id=None)

        payload = {
            "job_id": job.id,
            "session_id": command.session_id,
            "question": command.question,
        }
        try:
            message_id = await self._broker.publish(
                self._settings.stream_requests,
                payload,
                maxlen=self._settings.redis_stream_maxlen,
            )
        except Exception as exc:
            async with self._uow_factory() as uow:
                await uow.jobs.mark_failed(job.id, f"publish error: {exc}")
            raise

        async with self._uow_factory() as uow:
            await uow.jobs.set_message_id(job.id, message_id)

        return job.id

    async def process_question(self, command: ProcessQuestion) -> Answer:
        async with self._uow_factory() as uow:
            job = await uow.jobs.get(command.job_id)
            if job is None:
                raise JobNotFound(f"Job {command.job_id} не найден.")
            if job.status == JobStatus.DONE:
                return Answer(
                    text=job.answer or "",
                    sources=[],
                    rewritten_question=job.rewritten_question,
                )
            if job.status == JobStatus.FAILED:
                raise JobNotFound(f"Job {command.job_id} уже завершился с ошибкой.")

            started = await uow.jobs.mark_running(command.job_id)
            if not started:
                return Answer(text="", sources=[], rewritten_question=None)

            session = await uow.chat.get_session(command.session_id)
            if session is None:
                raise SessionNotFound(f"Чат-сессия {command.session_id} не найдена.")

            history = await uow.chat.get_history(command.session_id, limit=10)
            rewritten = await rewrite_question(
                command.question, history, self._llm, temperature=0.0
            )
            await uow.chat.add_message(
                ChatMessage(session_id=command.session_id, role=Role.USER, content=command.question)
            )

            sources: list[dict] = []
            if session.course_id is None:
                answer_text = NO_COURSE_ANSWER
            else:
                embedding = await self._embedder.embed(rewritten)
                chunks = await uow.chunks.search(
                    course_id=session.course_id,
                    embedding=embedding,
                    model_name=self._settings.embedding_model,
                    limit=self._settings.retrieval_top_k,
                )
                if not chunks:
                    answer_text = NO_MATERIALS_ANSWER
                else:
                    context = build_context(chunks)
                    answer_text = await generate_answer(
                        question=command.question,
                        context=context,
                        history=history,
                        llm=self._llm,
                        temperature=self._settings.llm_temperature,
                    )
                    sources = [_chunk_to_source(chunk) for chunk in chunks]

            chunk_ids = [source["chunk_id"] for source in sources]
            await uow.chat.add_message(
                ChatMessage(
                    session_id=command.session_id,
                    role=Role.ASSISTANT,
                    content=answer_text,
                    sources=sources or None,
                    used_chunk_ids=chunk_ids,
                )
            )
            await uow.jobs.mark_done(command.job_id, answer_text, sources, rewritten)
            return Answer(text=answer_text, sources=[], rewritten_question=rewritten)

    async def run_cron_task(self, command: RunCronTask) -> None:
        if command.name == "purge_terminal_jobs":
            days = int(command.payload.get("older_than_days", self._settings.job_retention_days))
            older_than = datetime.now(UTC) - timedelta(days=days)
            async with self._uow_factory() as uow:
                deleted = await uow.jobs.purge_terminal(older_than)
            logger.info(
                "cron_purge_terminal_jobs",
                deleted=deleted,
                older_than=older_than.isoformat(),
            )
            return
        raise ValueError(f"Неизвестная cron-задача: {command.name}")

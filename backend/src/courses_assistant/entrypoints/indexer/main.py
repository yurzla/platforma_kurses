"""Консьюмер очереди индексации описаний курсов."""

from __future__ import annotations

import asyncio
import contextlib
import signal

import structlog

from courses_assistant.adapters.persistence.course_indexer import CourseDescriptionIndexer
from courses_assistant.application.consumer import consume_loop
from courses_assistant.config import Settings, get_settings
from courses_assistant.container import Container, build_container

logger = structlog.get_logger(__name__)


class CourseIndexerWorker:
    def __init__(self, container: Container, settings: Settings) -> None:
        self._container = container
        self._settings = settings
        self._stop = asyncio.Event()
        self._indexer = CourseDescriptionIndexer(container.embedder, settings.embedding_model)

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        settings = self._settings
        logger.info("course_indexer_started", stream=settings.stream_index)
        await consume_loop(
            broker=self._container.broker,
            stream=settings.stream_index,
            group=settings.index_group,
            consumer=settings.index_consumer_name,
            stop=self._stop,
            handler=self._handle,
            block_ms=settings.stream_block_ms,
            reclaim_min_idle_ms=settings.consumer_pending_idle_ms,
            error_log_event="course_indexer_loop_error",
        )
        await self._container.close()
        logger.info("course_indexer_stopped")

    async def _handle(self, message_id: str, payload: dict) -> None:
        settings = self._settings
        kind = payload.get("kind", "course_description")
        identifier = payload.get("step_id" if kind == "step_upsert" else "course_id")
        if kind not in {"course_description", "step_upsert"} or not isinstance(identifier, int):
            await self._move_to_dead(message_id, payload, "bad payload")
            return
        try:
            async with self._container.session_factory() as session:
                indexed = (
                    await self._indexer.index_step(session, identifier)
                    if kind == "step_upsert"
                    else await self._indexer.index(session, identifier)
                )
                await session.commit()
            await self._container.broker.ack(
                settings.stream_index, settings.index_group, message_id
            )
            logger.info("content_indexed", kind=kind, identifier=identifier, found=indexed)
        except Exception as exc:  # noqa: BLE001
            await self._move_to_dead(message_id, payload, f"{type(exc).__name__}: {exc}")

    async def _move_to_dead(self, message_id: str, payload: dict, reason: str) -> None:
        settings = self._settings
        await self._container.broker.move_to_dead(
            settings.stream_index,
            settings.index_dlq,
            payload,
            reason,
            maxlen=settings.redis_stream_maxlen,
        )
        await self._container.broker.ack(settings.stream_index, settings.index_group, message_id)
        logger.error("course_index_failed", reason=reason, payload=payload)


async def _amain() -> None:
    settings = get_settings()
    container = build_container(settings)
    worker = CourseIndexerWorker(container, settings)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, worker.request_stop)
    await worker.run()


def main() -> None:
    asyncio.run(_amain())

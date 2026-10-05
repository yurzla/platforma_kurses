"""Асинхронный worker: читает очередь и обрабатывает вопросы."""

from __future__ import annotations

import asyncio
import contextlib
import signal

import structlog

from courses_assistant.application.commands import ProcessQuestion
from courses_assistant.application.consumer import consume_loop
from courses_assistant.config import Settings, get_settings
from courses_assistant.container import Container, build_container

logger = structlog.get_logger(__name__)


class Worker:
    def __init__(self, container: Container, settings: Settings) -> None:
        self._container = container
        self._settings = settings
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        settings = self._settings
        logger.info(
            "worker_started",
            stream=settings.stream_requests,
            group=settings.consumer_group,
        )
        await consume_loop(
            broker=self._container.broker,
            stream=settings.stream_requests,
            group=settings.consumer_group,
            consumer=settings.consumer_name,
            stop=self._stop,
            handler=self._handle,
            block_ms=settings.stream_block_ms,
            reclaim_min_idle_ms=settings.consumer_pending_idle_ms,
            error_log_event="worker_loop_error",
        )
        await self._container.close()
        logger.info("worker_stopped")

    async def _handle(self, message_id: str, payload: dict) -> None:
        settings = self._settings
        broker = self._container.broker
        job_id = payload.get("job_id")
        session_id = payload.get("session_id")
        question = payload.get("question")

        if not job_id or session_id is None or question is None:
            logger.error("worker_bad_payload", payload=payload)
            await broker.move_to_dead(
                settings.stream_requests,
                settings.stream_dead,
                payload,
                "bad payload",
                maxlen=settings.redis_stream_maxlen,
            )
            await broker.ack(settings.stream_requests, settings.consumer_group, message_id)
            return

        try:
            await self._container.bus.handle(
                ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
            )
            await broker.publish(
                settings.stream_events,
                {"event": "question.done", "job_id": job_id},
                maxlen=settings.redis_stream_events_maxlen,
            )
            await broker.ack(settings.stream_requests, settings.consumer_group, message_id)
            logger.info("job_done", job_id=job_id)
        except Exception as exc:  # noqa: BLE001
            await self._on_failure(message_id, payload, job_id, exc)

    async def _on_failure(
        self, message_id: str, payload: dict, job_id: str, exc: Exception
    ) -> None:
        settings = self._settings
        broker = self._container.broker

        attempts = await self._increment_attempts(job_id)
        if attempts >= settings.job_max_attempts:
            async with self._container.uow_factory() as uow:
                await uow.jobs.mark_failed(job_id, f"{type(exc).__name__}: {exc}")
            await broker.move_to_dead(
                settings.stream_requests,
                settings.stream_dead,
                payload,
                str(exc),
                maxlen=settings.redis_stream_maxlen,
            )
            await broker.ack(settings.stream_requests, settings.consumer_group, message_id)
            logger.error("job_failed", job_id=job_id, attempts=attempts, error=str(exc))
        else:
            await broker.ack(settings.stream_requests, settings.consumer_group, message_id)
            await broker.publish(
                settings.stream_requests, payload, maxlen=settings.redis_stream_maxlen
            )
            logger.warning("job_retry", job_id=job_id, attempts=attempts, error=str(exc))

    async def _increment_attempts(self, job_id: str) -> int:
        async with self._container.uow_factory() as uow:
            job = await uow.jobs.get(job_id)
            if job is None:
                return 0
            return await uow.jobs.increment_attempts(job_id)


async def _amain() -> None:
    settings = get_settings()
    settings.require_gigachat_credentials()
    container = build_container(settings)
    worker = Worker(container, settings)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, worker.request_stop)

    await worker.run()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()

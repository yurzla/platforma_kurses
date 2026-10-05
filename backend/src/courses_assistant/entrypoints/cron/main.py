"""Консьюмер отдельной cron-очереди rag.cron."""

from __future__ import annotations

import asyncio
import contextlib
import signal

import structlog

from courses_assistant.application.commands import RunCronTask
from courses_assistant.application.consumer import consume_loop
from courses_assistant.config import Settings, get_settings
from courses_assistant.container import Container, build_container

logger = structlog.get_logger(__name__)


class CronWorker:
    def __init__(self, container: Container, settings: Settings) -> None:
        self._container = container
        self._settings = settings
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        settings = self._settings
        logger.info(
            "cron_worker_started",
            stream=settings.stream_cron,
            group=settings.cron_group,
        )
        await consume_loop(
            broker=self._container.broker,
            stream=settings.stream_cron,
            group=settings.cron_group,
            consumer=settings.cron_consumer_name,
            stop=self._stop,
            handler=self._handle,
            block_ms=settings.stream_block_ms,
            reclaim_min_idle_ms=settings.consumer_pending_idle_ms,
            error_log_event="cron_loop_error",
        )
        await self._container.close()
        logger.info("cron_worker_stopped")

    async def _handle(self, message_id: str, payload: dict) -> None:
        settings = self._settings
        broker = self._container.broker
        name = payload.get("task")

        if not name:
            logger.error("cron_bad_payload", payload=payload)
            await broker.move_to_dead(
                settings.stream_cron,
                settings.cron_dlq,
                payload,
                "bad payload",
                maxlen=settings.redis_stream_maxlen,
            )
            await broker.ack(settings.stream_cron, settings.cron_group, message_id)
            return

        try:
            await self._container.bus.handle(RunCronTask(name=name, payload=payload))
            await broker.ack(settings.stream_cron, settings.cron_group, message_id)
            logger.info("cron_task_done", task=name)
        except Exception as exc:  # noqa: BLE001
            await broker.move_to_dead(
                settings.stream_cron,
                settings.cron_dlq,
                payload,
                f"{type(exc).__name__}: {exc}",
                maxlen=settings.redis_stream_maxlen,
            )
            await broker.ack(settings.stream_cron, settings.cron_group, message_id)
            logger.error("cron_task_failed", task=name, error=str(exc))


async def _amain() -> None:
    settings = get_settings()
    container = build_container(settings)
    worker = CronWorker(container, settings)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, worker.request_stop)

    await worker.run()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()

"""Планировщик: периодически публикует cron-задачи в отдельную очередь rag.cron."""

from __future__ import annotations

import asyncio
import contextlib
import signal

import structlog

from courses_assistant.config import Settings, get_settings
from courses_assistant.container import Container, build_container

logger = structlog.get_logger(__name__)

PURGE_TASK = "purge_terminal_jobs"


class Scheduler:
    def __init__(self, container: Container, settings: Settings) -> None:
        self._container = container
        self._settings = settings
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        settings = self._settings
        logger.info(
            "scheduler_started",
            stream=settings.stream_cron,
            interval_seconds=settings.cron_interval_seconds,
        )
        while not self._stop.is_set():
            payload = {
                "task": PURGE_TASK,
                "older_than_days": settings.job_retention_days,
            }
            await self._container.broker.publish(
                settings.stream_cron, payload, maxlen=settings.redis_stream_maxlen
            )
            logger.info("cron_task_scheduled", task=PURGE_TASK)
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(
                    self._stop.wait(), timeout=settings.cron_interval_seconds
                )
        await self._container.close()
        logger.info("scheduler_stopped")


async def _amain() -> None:
    settings = get_settings()
    container = build_container(settings)
    scheduler = Scheduler(container, settings)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, scheduler.request_stop)

    await scheduler.run()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()

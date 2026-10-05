"""Общий цикл чтения стрима через consumer group для воркеров."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import structlog

from courses_assistant.application.ports import MessageBroker

logger = structlog.get_logger(__name__)

MessageHandler = Callable[[str, dict], Awaitable[None]]


async def consume_loop(
    *,
    broker: MessageBroker,
    stream: str,
    group: str,
    consumer: str,
    stop: asyncio.Event,
    handler: MessageHandler,
    block_ms: int = 5000,
    reclaim_min_idle_ms: int = 60_000,
    reclaim_count: int = 10,
    error_log_event: str = "consumer_loop_error",
) -> None:
    """Читает сообщения группы и вызывает handler(message_id, payload).

    handler сам отвечает за ack/dlq. При ошибке чтения логирует и делает паузу.
    """
    await broker.ensure_group(stream, group)
    while not stop.is_set():
        try:
            messages = await broker.read_group(
                stream, group, consumer, count=1, block_ms=block_ms
            )
            if not messages:
                messages = await broker.reclaim_pending(
                    stream,
                    group,
                    consumer,
                    min_idle_ms=reclaim_min_idle_ms,
                    count=reclaim_count,
                )
            for message_id, payload in messages:
                await handler(message_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error(error_log_event, error=str(exc))
            await asyncio.sleep(1)

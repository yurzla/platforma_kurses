"""Интеграционные тесты Redis Streams (требуют Redis).

Запуск: INTEGRATION_REDIS_URL=redis://localhost:6379/15 pytest -m integration
"""

from __future__ import annotations

import os
import uuid

import pytest

from courses_assistant.adapters.broker.redis_streams import RedisStreamsBroker

REDIS_URL = os.getenv("INTEGRATION_REDIS_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not REDIS_URL, reason="INTEGRATION_REDIS_URL не задан"),
]


async def test_publish_consume_ack() -> None:
    assert REDIS_URL is not None
    broker = RedisStreamsBroker(REDIS_URL)
    suffix = uuid.uuid4().hex
    stream = f"test.requests.{suffix}"
    group = f"test-group-{suffix}"
    try:
        await broker.ensure_group(stream, group)
        await broker.publish(stream, {"job_id": "1", "session_id": 1, "question": "?"})

        messages = await broker.read_group(stream, group, "c1", count=10, block_ms=100)
        assert len(messages) == 1
        message_id, payload = messages[0]
        assert payload["job_id"] == "1"

        await broker.ack(stream, group, message_id)
        assert await broker.ping() is True
    finally:
        await broker.close()


async def test_read_group_blocks_longer_than_socket_timeout() -> None:
    """Блокирующее чтение не должно падать по socket-таймауту (redis-py default 5с)."""
    assert REDIS_URL is not None
    broker = RedisStreamsBroker(REDIS_URL)
    suffix = uuid.uuid4().hex
    stream = f"test.empty.{suffix}"
    group = f"test-group-{suffix}"
    try:
        await broker.ensure_group(stream, group)
        messages = await broker.read_group(stream, group, "c1", count=1, block_ms=6000)
        assert messages == []
    finally:
        await broker.close()

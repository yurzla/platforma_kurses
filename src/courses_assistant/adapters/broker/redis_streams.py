"""Redis Streams как шина сообщений (consumer groups, pending reclaim, DLQ)."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from courses_assistant.application.ports import MessageBroker


class RedisStreamsBroker(MessageBroker):
    def __init__(self, url: str, socket_timeout: float | None = None) -> None:
        self._client: redis.Redis = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=socket_timeout,
        )

    async def publish(self, stream: str, payload: dict) -> str:
        message_id = await self._client.xadd(stream, {"data": json.dumps(payload)})
        return str(message_id)

    async def ensure_group(self, stream: str, group: str) -> None:
        try:
            await self._client.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def read_group(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[tuple[str, dict]]:
        response = await self._client.xreadgroup(
            group, consumer, {stream: ">"}, count=count, block=block_ms
        )
        return self._parse(response)

    async def reclaim_pending(
        self,
        stream: str,
        group: str,
        consumer: str,
        min_idle_ms: int,
        count: int = 10,
    ) -> list[tuple[str, dict]]:
        response = await self._client.xautoclaim(
            stream, group, consumer, min_idle_time=min_idle_ms, start_id="0-0", count=count
        )
        messages = response[1] if len(response) > 1 else []
        return self._parse([[stream, messages]])

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        await self._client.xack(stream, group, message_id)

    async def move_to_dead(
        self, stream: str, dead_stream: str, payload: dict, reason: str
    ) -> None:
        dead_payload = {**payload, "error": reason, "source_stream": stream}
        await self._client.xadd(dead_stream, {"data": json.dumps(dead_payload)})

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _parse(response: Any) -> list[tuple[str, dict]]:
        result: list[tuple[str, dict]] = []
        if not response:
            return result
        for _stream, messages in response:
            for message_id, fields in messages:
                raw = fields.get("data")
                if raw is None:
                    continue
                result.append((str(message_id), json.loads(raw)))
        return result

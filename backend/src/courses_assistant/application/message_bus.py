"""Простой in-process message bus (cosmicpython)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

Command = TypeVar("Command")
Handler = Callable[[Any], Awaitable[Any]]


class MessageBus:
    def __init__(self, handlers: dict[type, Handler] | None = None) -> None:
        self._handlers: dict[type, Handler] = handlers or {}

    def register(self, command_type: type, handler: Handler) -> None:
        self._handlers[command_type] = handler

    async def handle(self, command: Any) -> Any:
        try:
            handler = self._handlers[type(command)]
        except KeyError as exc:  # pragma: no cover - defensive
            raise LookupError(f"Нет обработчика для команды {type(command)!r}") from exc
        return await handler(command)

"""Запуск API: python -m courses_assistant.entrypoints.api."""

from __future__ import annotations

import uvicorn

from courses_assistant.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "courses_assistant.entrypoints.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

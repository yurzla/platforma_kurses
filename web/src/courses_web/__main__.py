"""Запуск web-сервиса: python -m courses_web."""

from __future__ import annotations

import uvicorn

from courses_web.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "courses_web.app:create_app",
        factory=True,
        host=settings.web_host,
        port=settings.web_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

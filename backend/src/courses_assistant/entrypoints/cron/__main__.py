"""Запуск cron-консьюмера: python -m courses_assistant.entrypoints.cron."""

from __future__ import annotations

from courses_assistant.entrypoints.cron.main import main

if __name__ == "__main__":
    main()

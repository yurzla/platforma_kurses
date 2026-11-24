# Tasks

## 1. Автоматические правки

- [x] 1.1 Выполнить `uv run ruff check . --fix` и проверить, что остались только `E501`/`E702`

## 2. Ручные правки ruff

- [x] 2.1 Разбить длинные строки и `;`-statement в `routers/teacher.py`; проверить `uv run ruff check backend/src/courses_assistant/entrypoints/api/routers/teacher.py`
- [x] 2.2 Разбить длинные строки в `routers/admin.py`; проверить `uv run ruff check backend/src/courses_assistant/entrypoints/api/routers/admin.py`
- [x] 2.3 Разбить длинные строки в `web/routers/pages.py` и `api/app.py`; проверить `uv run ruff check .`

## 3. Mypy

- [x] 3.1 Исправить `rowcount` в `repositories.py` через `cast("CursorResult[Any]", ...)`
- [x] 3.2 Устранить конфликт `user`/`UserORM` в `routers/admin.py`; проверить `uv run mypy`

## 4. Проверка как в CI

- [x] 4.1 Прогнать `uv run ruff check .` и `uv run mypy`
- [x] 4.2 Прогнать `uv run pytest` с `INTEGRATION_DATABASE_URL` и `INTEGRATION_REDIS_URL`
- [x] 4.3 Проверить `uv lock --check` и обе Docker-сборки

## Workflow follow-up

- Закоммитить и запушить исправления в `feature/platform-development-merged`.
- Заархивировать change после зелёных проверок.

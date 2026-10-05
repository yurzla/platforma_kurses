## Context

Backend (`courses_assistant`) и web (`courses_web`) — два ASGI-приложения, но живут в одном пакете/образе/наборе зависимостей. Требуется развести их по коду, зависимостям и образам, сохранив HTTP-границу между ними.

## Goals / Non-Goals

- Goals: отдельные distribution'ы `courses-assistant` (backend) и `courses-web` (web); отдельные образы; web не тянет DB/Redis/LLM-библиотеки; корень — uv-workspace.
- Non-Goals: отдельный репозиторий; изменение HTTP-контракта API; разделение тестов по пакетам.

## Decisions

- **uv workspace**: корневой `pyproject.toml` — virtual root без `[project]`, только `[tool.uv.workspace] members=["backend","web"]` и общие tool-конфиги; один `uv.lock`.
- **Backend** остаётся в `backend/` как project `courses-assistant` со своими `alembic/`, `alembic.ini`, `Dockerfile`, scripts и dev-инструментами.
- **Web** — `web/` как project `courses-web` с минимальным набором (`fastapi`, `uvicorn[standard]`, `jinja2`, `httpx`, `structlog`, `pydantic-settings`, `python-multipart`); свои `config.py` и `middleware.py`; шаблоны/статика внутри пакета.
- **Docker**: контекст обоих образов — корень; `uv sync --frozen --no-dev --package <name>`. Фолбэк при несовместимости флагов — `uv export --package <name> --no-dev` + pip.
- **Alembic**: `uv run alembic -c backend/alembic.ini upgrade head`, `prepend_sys_path = backend/src`.
- **Compose**: `api/worker/cron/scheduler/migrate` — `backend/Dockerfile`; `web` — `web/Dockerfile` и только web-окружение.

## Risks / Trade-offs

- Virtual workspace root и dev-группа только в backend: `uv run ruff/mypy/pytest` из корня должны работать из общего venv. Проверяется первым шагом; фолбэк — добавить dev-группу и в web.
- `uv sync --package` в Docker может потребовать `--no-install-package` для второго члена; проверяется сборкой.
- Тесты остаются в корне и импортируют оба пакета — это dev-only связь, допустимо.

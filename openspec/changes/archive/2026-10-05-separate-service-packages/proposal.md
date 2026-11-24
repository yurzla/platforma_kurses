## Why

Backend (`courses_assistant`) и web (HTML/прокси) разделены на уровне ASGI-приложений, но остаются в одном пакете, одном образе и одном наборе зависимостей: web-контейнер тянет SQLAlchemy/pgvector/redis/LLM, а backend-код лежит рядом с корневыми конфигами. Нужны независимые сервисы (код, зависимости, образы).

## What Changes

- Backend переезжает в `backend/` (distribution `courses-assistant`), web — в `web/` (distribution `courses-web`); корень становится uv-workspace (`members = ["backend", "web"]`).
- Отдельные Dockerfile'ы (`backend/Dockerfile`, `web/Dockerfile`) и минимальный набор зависимостей у web (без DB/Redis/LLM).
- Web получает собственные `config.py` и `middleware.py`; backend — без web-переменных.
- Compose: сервис `web` не получает DB/Redis/GIGACHAT/ADMIN-окружение.

## Capabilities

### New Capabilities
<!-- нет -->

### Modified Capabilities
- `platform-health`: конфигурация разделяется по сервисам; backend и web собираются отдельными образами с разными наборами зависимостей.

## Impact

- Структура: `backend/{src,alembic,alembic.ini,Dockerfile,pyproject.toml}`, `web/{src,Dockerfile,pyproject.toml}`.
- Корневой `pyproject.toml` → virtual workspace root; tool-конфиги остаются в корне.
- `docker-compose.yml`, CI, `Makefile`, `ruff`/`mypy`-пути, README/AGENTS.
- Тесты остаются в корневом `tests/` и импортируют оба пакета (dev-окружение).

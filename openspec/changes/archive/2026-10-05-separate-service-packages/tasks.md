## 1. OpenSpec

- [x] 1.1 Change создан, delta `platform-health` валидна (`openspec validate separate-service-packages --strict`).

## 2. Перенос структуры

- [x] 2.1 `git mv src backend/src`; `git mv alembic backend/alembic`; `git mv alembic.ini backend/alembic.ini`; `git mv Dockerfile backend/Dockerfile`.
- [x] 2.2 `git mv src/courses_assistant/entrypoints/web web/src/courses_web` (путь внутри backend/src после переноса — `backend/src/courses_assistant/entrypoints/web`).

## 3. Метаданные и зависимости

- [x] 3.1 `backend/pyproject.toml`: project `courses-assistant`, scripts (без `courses-assistant-web`), dev-группа.
- [x] 3.2 `web/pyproject.toml`: project `courses-web`, минимальные runtime-deps.
- [x] 3.3 Корневой `pyproject.toml`: `[tool.uv.workspace]` + tool-конфиги; убрать `jinja2`/`python-multipart` из backend; `uv lock`.

## 4. Конфиг и middleware

- [x] 4.1 `courses_web/config.py` (`app_env`, `log_level`, `web_host`, `web_port`, `api_base_url`).
- [x] 4.2 `courses_web/middleware.py`; обновить импорты web.
- [x] 4.3 Убрать `api_base_url`/`web_host`/`web_port` из backend `config.py`.

## 5. Docker / Compose / CI

- [x] 5.1 `backend/Dockerfile` (EXPOSE 5000, `COPY backend/src`, alembic).
- [x] 5.2 `web/Dockerfile` (EXPOSE 8000, `--package courses-web`).
- [x] 5.3 `docker-compose.yml`: build по dockerfile'ам; web-окружение без DB/Redis/LLM/ADMIN.
- [x] 5.4 CI: ruff/mypy из корня, `alembic -c backend/alembic.ini`, pytest, сборка обоих образов; `Makefile`.

## 6. Тесты и тулинг

- [x] 6.1 `tests/web` импортирует `courses_web.app` и web-`Settings`.
- [x] 6.2 ruff `src=["backend/src","web/src","tests"]`; mypy `mypy_path="backend/src:web/src"`, `packages=["courses_assistant","courses_web"]`.

## 7. Документация и архив

- [x] 7.1 README/AGENTS: структура, независимые образы/зависимости.
- [x] 7.2 `ruff → mypy → pytest` (+ integration), сборка образов, compose-smoke.
- [x] 7.3 `openspec archive separate-service-packages -y`; `openspec validate --all --strict`.

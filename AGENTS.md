# AGENTS.md

RAG-ассистент образовательной платформы. uv-workspace из двух сервисов: backend
(`backend/src/courses_assistant/`, distribution `courses-assistant`) и web
(`web/src/courses_web/`, distribution `courses-web`). Clean Architecture в backend
(`domain ← application ← adapters ← entrypoints`); медленная генерация вынесена в worker-ы
(Redis Streams), HTTP отдаёт `202` + job_id. PostgreSQL+pgvector, GigaChat (LLM), Ollama
(embeddings). Подробности: `README.md`, схема БД: `docs/DB_SCHEMA.md`.

## Команды (всё через uv)

```bash
uv sync                                   # + обновляет uv.lock
make lint                                 # ruff check .
make typecheck                            # uv run mypy  (запускать БЕЗ аргументов)
make test                                 # весь pytest (интеграционные сами скипаются)
make test-unit                            # uv run pytest -m "not integration"
make test-integration                     # нужны INTEGRATION_DATABASE_URL и INTEGRATION_REDIS_URL
uv run pytest tests/unit/test_handlers.py::test_name   # один тест
make up / make logs / make down           # docker compose
uv run python -m courses_assistant.scripts.create_user --email s@x.io --password pw
uv run python -m courses_assistant.scripts.import_step_sources --token "$access_token"
```

Порядок перед завершением задачи: `lint → typecheck → test`.

Интеграционные тесты молча скипаются без env:
`INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edu_platform_kurses`
и `INTEGRATION_REDIS_URL=redis://localhost:6379/15` (Postgres с pgvector + Redis должны быть подняты).

## Тулчейн

- Python `>=3.12`, ruff/mypy `target-version = py312`; но `.python-version` и CI используют 3.13.
- uv-workspace: корневой `pyproject.toml` — virtual root (`[tool.uv.workspace] members=["backend","web"]`)
  + общие tool-конфиги; один `uv.lock`. Runtime-зависимости — в `[project].dependencies` своего пакета,
  инструменты — в `backend/[dependency-groups].dev`. Образы собираются `uv sync --frozen --no-dev
  --package courses-assistant|courses-web` (web без DB/Redis/LLM). CI делает `uv sync --frozen` —
  коммитить `uv.lock`.
- `uv run mypy` читает конфиг из корневого `pyproject.toml`
  (`packages=["courses_assistant","courses_web"]`, `mypy_path="backend/src:web/src"`).
- ruff: line-length 100, `src=["backend/src","web/src","tests"]`; для `backend/alembic/versions/*.py`
  E501 отключён.
- Единственная обязательная переменная для старта API — `GIGACHAT_CREDENTIALS` (иначе понятная ошибка).
  Compose переопределяет `DATABASE_URL`/`REDIS_URL`/`OLLAMA_URL` на service-hostnames.

## Архитектура и wiring

- Границы: `domain` не импортирует адаптеры/фреймворки; `application` знает только порты;
  адаптеры реализуют порты; entrypoints собираются в `backend/src/courses_assistant/container.py`.
- Новый сценарий: команда в `application/commands.py` → обработчик в `application/handlers.py` →
  регистрация в `MessageBus` внутри `container.py`. Порт — в `application/ports.py`.
- У каждого порта есть фейк в `tests/fakes.py` — обновляй его при изменении порта.
- API-тесты используют `httpx.ASGITransport` и `build_test_container` из `tests/api/test_api.py`.
- Разделение сервисов: backend `entrypoints/api` — JSON-бэкенд (:5000, auth/chat/jobs/catalog/admin);
  web-пакет `courses_web` (:8000) — Jinja2-страницы + прозрачный прокси `/api/*` (httpx, cookie
  пробрасываются). Шаблоны/статика web — `web/src/courses_web/{templates,static}`, вход и роли —
  переключатель Админ/Студент на `/login`. Web имеет свой `courses_web/{config,middleware}.py` и
  НЕ импортирует `courses_assistant`.
- Web-тесты: `tests/web/test_web.py` (web-стек поверх API через `httpx.ASGITransport`).
- Аутентификация (API): admin — `ADMIN_USERNAME`/`ADMIN_PASSWORD`; student — `users` +
  `domain/security.py` (scrypt). Сессия — `SessionMiddleware`, ключи в `api/dependencies.py`.

## БД и миграции

- Alembic: `backend/alembic/versions/` (baseline 14 таблиц → HNSW → jobs → updated_at index →
  step_sources). Baseline не пересоздавать (в `_LATER_TABLES` исключены `jobs`, `step_sources`).
- Идемпотентный bootstrap: `uv run python -m courses_assistant.scripts.db_bootstrap`
  (stamp baseline при наличии дампа + upgrade).
- Демо-дамп опционален и gitignored: `tmp/edu_platform_kurses.sql`; compose `seed` использует
  `postgres:18-alpine`, сервер — `pgvector/pgvector:pg17`.

## OpenSpec (обязательно для изменений поведения)

Поведение описано в `openspec/specs/<capability>/spec.md`; используй навыки/команды `.opencode`
(`openspec-propose` → `openspec-apply-change` → `openspec-archive-change`).

```bash
openspec new change <name>                                   # НЕ `openspec change new`
openspec instructions <proposal|specs|design|tasks> --change <name> --json
openspec validate <name> --strict                            # флаг позиционный, `--change` нет
openspec validate --all --strict
openspec archive <name> -y                                   # синкает дельты в openspec/specs/
```

Грабли дельт: сценарии строго `#### Scenario:` (4 решётки); `## MODIFIED Requirements` обязан
повторять весь текущий блок требования со всеми сценариями, иначе validate/archive падает;
для переименования требования используй `## REMOVED` + `## ADDED` (вариант RENAMED+MODIFIED
ломает проверку сохранения сценариев). Новой capability нужен `## Purpose`.

## Гочи

- Блокирующее чтение Redis: у `XREADGROUP` нельзя ставить `socket_timeout` (дефолт redis-py 5s
  роняет холостое чтение) — использовать `STREAM_BLOCK_MS`.
- `GIGACHAT_BASE_URL` должен указывать на JSON API (`https://api.giga.chat/v1`);
  `https://giga.chat/v1` отдаёт HTML со статусом 200.
- Вход в админку опционален: задать одновременно `ADMIN_USERNAME` и `ADMIN_PASSWORD`
  (форма `/login` в web, подписанная session-cookie); пусто → `/dashboard` и `/api/v1/admin/*` открыты.
- Порты: API `5000`, web `8000` (`API_PORT`/`WEB_PORT`), web ходит в API по `API_BASE_URL`.
- Ключи ответов тестов: в дампе Stepik `block.options` их нет — только `/api/step-sources`
  (нужен токен автора курса; иначе шаги `grading=manual`). Импорт — `import_step_sources`.
- Реальные секреты в `.env.example` не коммитить (только плейсхолдеры); `.env` в `.gitignore`.

## CI

`.github/workflows/ci.yml`: `lint` (ruff+mypy), `test` (services pgvector pg17 + redis,
`alembic -c backend/alembic.ini upgrade head`, pytest), `build` (`docker build` обоих образов).
Дублировать проверки локально не нужно.

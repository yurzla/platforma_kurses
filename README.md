# Courses Assistant

RAG-ассистент для образовательной платформы: отвечает студенту на вопросы по материалам курса.
Спроектирован по Clean Architecture (cosmicpython): медленная генерация вынесена в асинхронные
worker-ы, HTTP API отдаёт `202` и job-id, клиент опрашивает статус.

## Архитектура

```
browser ──► web (courses_web, HTML/Jinja2, :8000) ──HTTP──► backend api (JSON, :5000)
                                                                │
backend worker ─────────────────────────────────────────────────┤
backend cron ───────────────────────────────────────────────────┼── application
backend scheduler ──────────────────────────────────────────────┘        │
                                                                         ▼
                                         adapters (SQLAlchemy, GigaChat, Ollama, Redis Streams)
                                                                         │
                                                                    domain
```

Репозиторий — uv-workspace из двух независимых сервисов: `backend/` (distribution
`courses-assistant`) и `web/` (distribution `courses-web`). `web` — только
визуализация и прозрачный прокси `/api/*` к API (cookie сессии пробрасываются);
он не зависит от БД/Redis/LLM и собирается отдельным образом. Аутентификация
(админ и студент) живёт в API.

Поток обработки вопроса:

```
POST /ask → jobs(queued) в PostgreSQL → XADD rag.requests → 202 {job_id}
worker → XREADGROUP → status=running → rewrite → embed → pgvector <=> → GigaChat
       → в одной транзакции: сообщения + jobs(done) → XACK
       → ошибка: ретраи → rag.dead (DLQ)
GET /jobs/{id} → queued | running | done | failed
scheduler → XADD rag.cron (purge_terminal_jobs) → cron-worker:
       удаляет старые done/failed job-ы → XACK (ошибка → rag.cron.dead)
```

Технологии: FastAPI, SQLAlchemy 2.0 async + asyncpg, pgvector, Alembic, Redis Streams,
GigaChat (httpx, OAuth), Ollama `nomic-embed-text` (768), uv, Docker Compose, pytest.

## Структура

```
backend/                          distribution courses-assistant
  pyproject.toml  Dockerfile  alembic.ini
  src/courses_assistant/
    domain/         модели, ошибки, промпты, построение контекста
    application/    ports, unit_of_work, message_bus, commands, queries, handlers, rag, consumer
    adapters/       persistence (orm, repositories, uow), llm/gigachat, embeddings/ollama,
                    broker/redis_streams
    entrypoints/    api (JSON), worker, cron, scheduler
    scripts/        db_bootstrap, stepik_dump, load_stepik, embed_chunks,
                    create_user, import_step_sources
  alembic/          baseline (14 таблиц) + HNSW + jobs + updated_at index + step_sources
web/                              distribution courses-web
  pyproject.toml  Dockerfile
  src/courses_web/  app, config, client, middleware, routers (pages, proxy), templates, static
pyproject.toml                    uv-workspace root (members = backend, web) + tool-конфиги
tests/                            unit, integration, api, web, fakes
```

## Требования

- Python 3.12+ (проект собран под 3.13)
- [uv](https://docs.astral.sh/uv/)
- Docker + Docker Compose (для инфраструктуры)

## Быстрый старт

```bash
uv sync
cp .env.example .env      # заполнить GIGACHAT_CREDENTIALS
make test-unit            # юнит/API-тесты без внешних сервисов
```

## Запуск инфраструктуры

```bash
# опционально: положить демо-дамп в tmp/edu_platform_kurses.sql
make up                   # docker compose up --build -d
curl http://localhost:5000/health   # API
curl http://localhost:8000/health   # web
make logs
make down
```

Compose поднимает `postgres` (pgvector), `redis`, `ollama` (+ pull модели), `seed`
(загрузка дампа, если `tmp/edu_platform_kurses.sql` существует), `migrate`
(Alembic: stamp baseline при наличии дампа + upgrade), `api` (:5000), `web` (:8000),
`worker`, `scheduler` (периодически ставит cron-задачи) и `cron` (выполняет их).

## Web-интерфейс

Web-сервис: `http://localhost:8000` — обучение и админка.

- **Студент**: `/login` (вкладка «Студент») → `/courses` → курс → шаг (тесты,
  автопроверка, прогресс) + RAG-панель «Ассистент».
- **Администратор**: `/login` (вкладка «Администратор») → `/dashboard` — вкладки
  Jobs / DLQ / Streams, фильтры, авто-обновление. Переключатель роли — на странице
  входа; кнопка «Тема» переключает светлую/тёмную тему (localStorage).
- Web — только визуализация: данные берёт у API через прокси `/api/*`, cookie
  сессии пробрасываются как есть.

Доступ администратора: если заданы `ADMIN_USERNAME` и `ADMIN_PASSWORD`, вход
обязателен (сессия в подписанной cookie); пусто — админ-доступ открыт.
Студенты входят по email/паролю из таблицы `users` (см. `scripts/create_user.py`).

## Ретенция

- **Redis-стримы** ограничены approximate-`MAXLEN` (`REDIS_STREAM_MAXLEN`,
  `REDIS_STREAM_EVENTS_MAXLEN`) — рост стримов ограничен.
- **Postgres `jobs`**: cron-задача `purge_terminal_jobs` раз в
  `CRON_INTERVAL_SECONDS` удаляет завершённые (`done`/`failed`) job-ы старше
  `JOB_RETENTION_DAYS`. История (`chat_messages`/`chat_sessions`) не удаляется.

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/auth/admin/login` | вход администратора (JSON) → сессия |
| POST | `/api/v1/auth/admin/logout` | выход администратора |
| POST | `/api/v1/auth/student/login` | вход студента (`email`, `password`) |
| POST | `/api/v1/auth/student/logout` | выход студента |
| GET | `/api/v1/auth/me` | текущий пользователь (`role`, `id`, `name`, `email`) |
| POST | `/api/v1/chat/sessions` | создать сессию (`course_id`, опц. `user_id`) → 201 |
| GET | `/api/v1/chat/sessions/{id}/messages?limit=` | история сообщений |
| POST | `/api/v1/chat/sessions/{id}/ask` | задать вопрос → 202 `{job_id}` |
| GET | `/api/v1/jobs/{job_id}` | статус job и ответ |
| GET | `/api/v1/courses` | список курсов студента (с прогрессом) |
| GET | `/api/v1/courses/{id}` | курс: секции/уроки/шаги |
| GET | `/api/v1/courses/{id}/steps/{step_id}` | шаг (без правильных ответов) |
| POST | `/api/v1/courses/{id}/steps/{step_id}/answer` | ответ → проверка и прогресс |
| GET | `/health`, `/health/ready` | liveness / readiness |
| GET | `/api/v1/admin/overview` | счётчики job по статусам + метрики стримов |
| GET | `/api/v1/admin/jobs` | список job-ов (`status`, `session_id`, `search`, `limit`, `offset`) |
| GET | `/api/v1/admin/jobs/{id}` | детали job |
| GET | `/api/v1/admin/dlq` | записи DLQ (`rag.dead`, `rag.cron.dead`) |
| GET | `/api/v1/admin/streams` | метрики Redis Streams |

Web-страницы (порт 8000): `/login`, `/logout`, `/dashboard`, `/courses`,
`/courses/{id}`, `/courses/{id}/steps/{step_id}`, `/health`.

Swagger API: `http://localhost:5000/docs`.

## Миграции

```bash
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini revision --autogenerate -m "message"
uv run python -m courses_assistant.scripts.db_bootstrap   # идемпотентный bootstrap
```

## Скрипты импорта

```bash
uv run python -m courses_assistant.scripts.stepik_dump --output stepik_dump
uv run python -m courses_assistant.scripts.load_stepik --dump-dir stepik_dump
uv run python -m courses_assistant.scripts.embed_chunks
# ключи ответов тестов (нужен токен с доступом к step-sources):
uv run python -m courses_assistant.scripts.import_step_sources --token "$access_token"
# пользователь (студент/админ):
uv run python -m courses_assistant.scripts.create_user \
    --email s@example.com --password secret --name "Студент"
```

## Разработка

```bash
make lint        # ruff
make typecheck   # mypy
make test        # pytest (integration-skipped без сервисов)
make cov
```

Интеграционные тесты:

```bash
INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edu_platform_kurses \
INTEGRATION_REDIS_URL=redis://localhost:6379/15 \
make test-integration
```

## Переменные окружения

См. `.env.example`. Ключевые: `DATABASE_URL`, `REDIS_URL`, `OLLAMA_URL`,
`EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `GIGACHAT_CREDENTIALS`, `GIGACHAT_AUTH_URL`,
`GIGACHAT_BASE_URL`, `GIGACHAT_MODEL`.

Сервисы: `API_PORT` (:5000), `WEB_PORT` (:8000), `API_BASE_URL` (URL API для web,
в compose — `http://api:5000`).

Планировщик/ретенция/админка: `STREAM_CRON`, `CRON_INTERVAL_SECONDS`,
`JOB_RETENTION_DAYS`, `REDIS_STREAM_MAXLEN`, `REDIS_STREAM_EVENTS_MAXLEN`,
`ADMIN_USERNAME`/`ADMIN_PASSWORD` (пусто — админ-доступ открыт),
`ADMIN_SESSION_SECRET`, `ADMIN_COOKIE_SECURE`.

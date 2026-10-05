# Courses Assistant

RAG-ассистент для образовательной платформы: отвечает студенту на вопросы по материалам курса.
Спроектирован по Clean Architecture (cosmicpython): медленная генерация вынесена в асинхронные
worker-ы, HTTP API отдаёт `202` и job-id, клиент опрашивает статус.

## Архитектура

```
entrypoints/api (FastAPI) ──┐
entrypoints/worker ─────────┤
entrypoints/cron ───────────┼── application (commands, handlers, queries, ports, message bus, consumer)
entrypoints/scheduler ──────┘                 │
                                              ▼
                                      adapters (SQLAlchemy, GigaChat, Ollama, Redis Streams)
                                              │
                                         domain (модели, промпты, контекст)
```

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
src/courses_assistant/
  domain/         модели, ошибки, промпты, построение контекста
  application/    ports, unit_of_work, message_bus, commands, queries, handlers, rag, consumer
  adapters/       persistence (orm, repositories, uow), llm/gigachat, embeddings/ollama, broker/redis_streams
  entrypoints/    api (FastAPI + dashboard на Jinja2), worker, cron, scheduler
  scripts/        db_bootstrap, stepik_dump, load_stepik, embed_chunks
alembic/          baseline (14 таблиц) + HNSW + jobs + updated_at index
tests/            unit, integration, api, fakes
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
curl http://localhost:8000/health
make logs
make down
```

Compose поднимает `postgres` (pgvector), `redis`, `ollama` (+ pull модели), `seed`
(загрузка дампа, если `tmp/edu_platform_kurses.sql` существует), `migrate`
(Alembic: stamp baseline при наличии дампа + upgrade), `api`, `worker`, `scheduler`
(периодически ставит cron-задачи) и `cron` (выполняет их).

## Дашборд

Веб-дашборд: `http://localhost:8000/dashboard` — вкладки Jobs / DLQ / Streams,
фильтры по статусу/сессии/вопросу, авто-обновление. Данные отдаёт read-only API
`/api/v1/admin/*`.

Если задан `ADMIN_TOKEN`, доступ к дашборду и админ-API требует токен:
`http://localhost:8000/dashboard?token=<ADMIN_TOKEN>` (токен сохраняется в cookie)
либо заголовок `Authorization: Bearer <ADMIN_TOKEN>` для API.

## Ретенция

- **Redis-стримы** ограничены approximate-`MAXLEN` (`REDIS_STREAM_MAXLEN`,
  `REDIS_STREAM_EVENTS_MAXLEN`) — рост стримов ограничен.
- **Postgres `jobs`**: cron-задача `purge_terminal_jobs` раз в
  `CRON_INTERVAL_SECONDS` удаляет завершённые (`done`/`failed`) job-ы старше
  `JOB_RETENTION_DAYS`. История (`chat_messages`/`chat_sessions`) не удаляется.

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/chat/sessions` | создать сессию (`user_id`, `course_id`) → 201 |
| GET | `/api/v1/chat/sessions/{id}/messages?limit=` | история сообщений |
| POST | `/api/v1/chat/sessions/{id}/ask` | задать вопрос → 202 `{job_id}` |
| GET | `/api/v1/jobs/{job_id}` | статус job и ответ |
| GET | `/health`, `/health/ready` | liveness / readiness |
| GET | `/dashboard` | веб-дашборд (Jobs / DLQ / Streams) |
| GET | `/api/v1/admin/overview` | счётчики job по статусам + метрики стримов |
| GET | `/api/v1/admin/jobs` | список job-ов (`status`, `session_id`, `search`, `limit`, `offset`) |
| GET | `/api/v1/admin/jobs/{id}` | детали job |
| GET | `/api/v1/admin/dlq` | записи DLQ (`rag.dead`, `rag.cron.dead`) |
| GET | `/api/v1/admin/streams` | метрики Redis Streams |

Swagger: `http://localhost:8000/docs`.

## Миграции

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"
uv run python -m courses_assistant.scripts.db_bootstrap   # идемпотентный bootstrap
```

## Скрипты импорта

```bash
uv run python -m courses_assistant.scripts.stepik_dump --output stepik_dump
uv run python -m courses_assistant.scripts.load_stepik --dump-dir stepik_dump
uv run python -m courses_assistant.scripts.embed_chunks
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

Планировщик/ретенция/админка: `STREAM_CRON`, `CRON_INTERVAL_SECONDS`,
`JOB_RETENTION_DAYS`, `REDIS_STREAM_MAXLEN`, `REDIS_STREAM_EVENTS_MAXLEN`,
`ADMIN_TOKEN` (пусто — доступ к дашборду открыт).

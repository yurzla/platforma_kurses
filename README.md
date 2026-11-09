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
                    create_user, import_step_sources, cleanup_empty_steps,
                    renumber_steps
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

- **Вход** (`/login`) — единая форма email+password; роль определяется сервером.
- **Регистрация** (`/register`) — самостоятельная, с ролью `student` или
  `teacher`; роль `admin` при регистрации недоступна.
- **Обучение**: `/courses` → курс → шаг (тесты, автопроверка, прогресс) +
  RAG-панель «Ассистент»; на страницах списков (`/courses`, `/my-courses`) панель
  показывает историю чатов по курсам, а новый вопрос ищет материалы сразу по всем
  курсам и может порекомендовать курсы из каталога платформы; на странице курса/шага
  история и ответы ограничены текущим курсом.
- **Администратор**: `/dashboard` («Админ панель») — вкладки Jobs / DLQ / Streams /
  Пользователи, фильтры, авто-обновление; на вкладке «Пользователи» можно выдавать
  роли (`student`/`teacher`/`admin`). Кнопка «Тема» переключает светлую/тёмную
  тему (localStorage).
- Web — только визуализация: данные берёт у API через прокси `/api/*`, cookie
  сессии пробрасываются как есть.

Права определяются ролью пользователя из таблицы `users` (`student`/`teacher`/`admin`),
а не переменными окружения. Все входят по email/паролю; администратор создаётся
только скриптом (см. `scripts/create_user.py`), а дальше роли выдаются на вкладке
«Пользователи». Админ не может менять собственную роль.

## Ретенция

- **Redis-стримы** ограничены approximate-`MAXLEN` (`REDIS_STREAM_MAXLEN`,
  `REDIS_STREAM_EVENTS_MAXLEN`) — рост стримов ограничен.
- **Postgres `jobs`**: cron-задача `purge_terminal_jobs` раз в
  `CRON_INTERVAL_SECONDS` удаляет завершённые (`done`/`failed`) job-ы старше
  `JOB_RETENTION_DAYS`. История (`chat_messages`/`chat_sessions`) не удаляется.

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/auth/register` | регистрация (`email`, `name`, `password`, `role` = student/teacher) → сессия |
| POST | `/api/v1/auth/login` | вход (`email`, `password`) → сессия |
| POST | `/api/v1/auth/logout` | выход |
| GET | `/api/v1/auth/me` | текущий пользователь (`role`, `id`, `name`, `email`) |
| POST | `/api/v1/chat/sessions` | создать сессию (`course_id`, опц.; без него — по всем курсам) → 201 |
| GET | `/api/v1/chat/sessions` | сессии пользователя: курс, время старта, превью последнего сообщения |
| GET | `/api/v1/chat/sessions/{id}/messages?limit=` | история сообщений |
| POST | `/api/v1/chat/sessions/{id}/ask` | задать вопрос → 202 `{job_id}` |
| GET | `/api/v1/jobs/{job_id}` | статус job и ответ |
| GET | `/api/v1/courses` | список курсов: `enrolled`, `limit` (1..200), `offset` → `{items,total,limit,offset}` |
| GET | `/api/v1/courses/{id}` | курс: секции/уроки/шаги |
| GET | `/api/v1/courses/{id}/steps/{step_id}` | шаг (без правильных ответов) |
| POST | `/api/v1/courses/{id}/steps/{step_id}/answer` | ответ → проверка и прогресс |
| GET | `/health`, `/health/ready` | liveness / readiness |
| GET | `/api/v1/admin/overview` | счётчики job по статусам + метрики стримов |
| GET | `/api/v1/admin/jobs` | список job-ов (`status`, `session_id`, `search`, `limit`, `offset`) |
| GET | `/api/v1/admin/jobs/{id}` | детали job |
| GET | `/api/v1/admin/dlq` | записи DLQ (`rag.dead`, `rag.cron.dead`) |
| GET | `/api/v1/admin/streams` | метрики Redis Streams |
| GET | `/api/v1/admin/users` | список пользователей (`search`, `limit`, `offset`) |
| PATCH | `/api/v1/admin/users/{id}` | смена роли пользователя (`role`) |

Web-страницы (порт 8000): `/login`, `/logout`, `/dashboard`, `/courses`,
`/my-courses`, `/courses/{id}`, `/courses/{id}/steps/{step_id}`, `/health`.

### Формат списка курсов (BREAKING)

`GET /api/v1/courses` возвращает объект-конверт вместо массива:

```json
{
  "items": [{ "id": 10, "title": "...", "enrolled": true, "progress_percent": 40.0, "...": "..." }],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

Параметры: `enrolled=true` — только курсы с прогрессом пользователя; `limit` (по умолчанию 50,
1..200) и `offset` (по умолчанию 0). Web-страницы `/courses` и `/my-courses` запрашивают по 10
курсов и нумеруют страницы через `?page=N` (1-based), пересчитывая в `limit/offset`.

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

JWT: `JWT_SECRET` (ключ подписи access-токена; пусто — эфемерный на процесс),
`JWT_ALGORITHM`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL`, `COOKIE_SECURE`.
Access и refresh передаются в httpOnly cookie; refresh-токены хранятся в БД
(таблица `refresh_tokens`) и ротируются на `/api/v1/auth/refresh`.

Пароли: обратимое шифрование Fernet ключом `PASSWORD_KEY` из `.env`
(urlsafe-base64; пусто — операции с паролями завершаются ошибкой). Ключ и
сгенерированные пароли не коммитятся. Сброс паролей всех пользователей:

```bash
uv run python -m courses_assistant.scripts.reset_passwords --file .secrets/passwords.txt
```

Скрипт выдаёт новые случайные пароли, шифрует их, отзывает refresh-токены и
пишет логины с паролями в `.secrets/passwords.txt` (права `600`, каталог в
`.gitignore`).

Планировщик/ретенция: `STREAM_CRON`, `CRON_INTERVAL_SECONDS`, `JOB_RETENTION_DAYS`,
`REDIS_STREAM_MAXLEN`, `REDIS_STREAM_EVENTS_MAXLEN`.

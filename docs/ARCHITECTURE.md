# Архитектура Courses Assistant

Документ описывает фактическое устройство системы по коду (а не по планам):
компоненты, слои, очереди, фоновые задачи и два ключевых бизнес-сценария —
RAG-ответ ассистента и подбор курсов. Схема БД — в [`DB_SCHEMA.md`](DB_SCHEMA.md).

Оглавление:

1. [Назначение и стек](#1-назначение-и-стек)
2. [Компонентная диаграмма](#2-компонентная-диаграмма)
3. [Сервисы и образы Docker Compose](#3-сервисы-и-образы-docker-compose)
4. [Слои и зависимости](#4-слои-и-зависимости)
5. [Очереди и воркеры](#5-очереди-и-воркеры)
6. [Асинхронные задачи](#6-асинхронные-задачи)
7. [Флоу ассистента (RAG-ответ)](#7-флоу-ассистента-rag-ответ)
8. [Как источники подаются в модель](#8-как-источники-подаются-в-модель)
9. [Релевантность и отбор источников](#9-релевантность-и-отбор-источников)
10. [Флоу рекомендаций курсов](#10-флоу-рекомендаций-курсов)
11. [Индексация контента](#11-индексация-контента)
12. [Конфигурация](#12-конфигурация)

---

## 1. Назначение и стек

RAG-ассистент образовательной платформы: отвечает студенту по материалам курса,
подбирает курсы по семантике запроса, ведет обучение (каталог, шаги, автопроверка,
прогресс), кабинет преподавателя и админку.

Медленная генерация вынесена из HTTP: API ставит задачу в очередь и возвращает
`202` + `job_id`, клиент опрашивает статус.

| Слой | Технологии |
|---|---|
| Backend (distribution `courses-assistant`) | Python 3.13, FastAPI, uvicorn, SQLAlchemy 2.0 async + asyncpg, Alembic, pgvector, redis-py (Streams), httpx + tenacity, pydantic v2 / pydantic-settings, structlog, PyJWT, cryptography (Fernet), fpdf2, typer |
| Web (distribution `courses-web`) | FastAPI, Jinja2, httpx, markdown-it-py, python-multipart, structlog |
| Инфраструктура | PostgreSQL 17 + pgvector (HNSW, pg_trgm), Redis 7 Streams, Ollama (`nomic-embed-text`, 768), GigaChat (`GigaChat-2`) |
| Инструменты | uv workspace (один `uv.lock`), ruff, mypy, pytest (+ pytest-asyncio, respx), Docker Compose, GitHub Actions |

## 2. Компонентная диаграмма

```
                              ┌──────────────────────────┐
                              │         Браузер          │
                              └────────────┬─────────────┘
                                           │ HTTP (HTML, cookie access/refresh)
                                           ▼
                      ┌────────────────────────────────────────┐
                      │ web :8000  (courses_web)               │
                      │ Jinja2-страницы + прозрачный прокси     │
                      │ /api/*, авто-refresh access-токена      │
                      └────────────┬───────────────────────────┘
                                   │ httpx (Cookie / Authorization)
                                   ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ api :5000  (FastAPI JSON)                                          │
   │ /auth /chat /jobs /courses /teacher /admin /preferences /health    │
   │ container.py → Handlers → UnitOfWork                               │
   └───┬───────────────┬──────────────────┬───────────────────┬────────┘
       │               │                  │                   │
       ▼               ▼                  ▼                   ▼
 ┌───────────┐  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐
 │ PostgreSQL│  │ Redis       │   │ GigaChat API │   │ Ollama         │
 │ +pgvector │  │ Streams     │   │ (LLM)        │   │ (embeddings)   │
 └─────▲─────┘  └──┬───────┬──┘   └──────▲───────┘   └───────▲────────┘
       │           │       │             │                   │
       │           │       └─────────────┼───────────────────┘
       │           │                     │
       │      ┌────▼──────────────┐      │
       │      │ worker            │──────┘  вопросы чата: rewrite + RAG + ответ
       │      ├───────────────────┤
       │      │ indexer           │  индексация описаний курсов и шагов
       │      ├───────────────────┤
       │      │ cron              │  purge_terminal_jobs
       │      ├───────────────────┤
       │      │ scheduler         │──── XADD rag.cron (раз в час)
       │      └───────────────────┘
       └────────────────────────────────────────────────────────────
              все фоновые процессы — тот же образ backend
```

Связи между сервисами — только HTTP (web → api) и Redis Streams (api → воркеры).
`courses_web` не импортирует `courses_assistant` и не знает про БД/Redis/LLM.

## 3. Сервисы и образы Docker Compose

`docker-compose.yml`:

| Сервис | Образ / сборка | Роль | Порт |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg17` | БД + расширение `vector`; volume `pgdata` | 5432 |
| `redis` | `redis:7-alpine` | Streams-брокер | 6379 |
| `ollama` | `ollama/ollama:latest` | локальные эмбеддинги; volume `ollama` | 11434 |
| `ollama-pull` | `ollama/ollama:latest` | one-shot: `ollama pull nomic-embed-text` | — |
| `seed` | `postgres:18-alpine` | one-shot: заливка `tmp/edu_platform_kurses.sql`, если БД пустая | — |
| `migrate` | build `backend/Dockerfile` | one-shot: `scripts.db_bootstrap` (stamp baseline + `alembic upgrade`) | — |
| `api` | build backend | uvicorn `:5000`, healthcheck `/health` | 5000 |
| `web` | build `web/Dockerfile` | uvicorn `:8000`, healthcheck `/health` | 8000 |
| `worker` | build backend | `python -m ...entrypoints.worker` | — |
| `indexer` | build backend | `python -m ...entrypoints.indexer` | — |
| `scheduler` | build backend | `python -m ...entrypoints.scheduler` | — |
| `cron` | build backend | `python -m ...entrypoints.cron` | — |

Оба Dockerfile — `python:3.13-slim` + `uv sync --frozen --no-dev --package ...`.
Web-образ не тянет БД/Redis/LLM-зависимости. Общие переменные окружения заданы
якорями `x-app-env`, сборки — `x-backend-build` / `x-web-build`.

Замечания:

- `seed` использует клиент `postgres:18-alpine` (не сервер), чтобы не плодить еще один серверный образ.
- `migrate` зависит от успешного `seed`; `api`/воркеры — от успешного `migrate`.

## 4. Слои и зависимости

Clean Architecture (cosmicpython): зависимости направлены внутрь.

```
entrypoints   api | worker | indexer | scheduler | cron
      │            (собираются в container.py — composition root)
      ▼
adapters      persistence (orm, repositories, uow, course_indexer)
              llm/gigachat, embeddings/ollama, broker/redis_streams,
              tokens/jwt, export/pdf
      │        (реализуют порты application)
      ▼
application   ports, commands/queries, handlers, message_bus,
              rag, recommendations, consumer, chat_export
      │
      ▼
domain        models, catalog, quiz, prompts, context, formatting,
              recommender, recommendations, video, security, errors
```

- **domain** — чистые функции и датаклассы без БД и фреймворков;
- **application** — use-cases и ABC-порты (знает только порты);
- **adapters** — SQLAlchemy, Redis, GigaChat, Ollama, JWT;
- **entrypoints** — FastAPI-роутеры и консьюмеры;
- **container.py** — единственное место сборки зависимостей.

Ключевые элементы application-слоя:

- `MessageBus` регистрирует команды: `CreateChatSession`, `SendQuestion`,
  `ProcessQuestion`, `RunCronTask`, `RegisterUser`, `ChangeUserRole`.
- `UnitOfWork` (`adapters/persistence/unit_of_work.py`) держит репозитории:
  `chat`, `chunks`, `jobs`, `users`, `catalog`, `refresh_tokens`, `preferences`,
  `recommender`.
- У каждого порта есть фейк в `tests/fakes.py`.

Второй сервис `courses_web` — сознательно тонкий: `app`, `config`, `client`
(проброс cookie + авто-refresh), `middleware`, `routers/pages`, `routers/proxy`,
`templates`, `static`.

## 5. Очереди и воркеры

Брокер — Redis Streams с consumer groups. Брокера задач типа Celery/ARQ нет.

| Stream | Группа / consumer | Кто слушает | Что делает | DLQ |
|---|---|---|---|---|
| `rag.requests` | `rag-workers` / `worker-1` | `worker` | `ProcessQuestion`: rewrite → RAG/рекомендации → ответ | `rag.dead` |
| `rag.index.requests` | `rag-indexers` / `indexer-1` | `indexer` | `course_description` и `step_upsert` | `rag.index.dead` |
| `rag.cron` | `rag-cron` / `cron-1` | `cron` | `purge_terminal_jobs` | `rag.cron.dead` |
| `rag.events` | `rag-workers` | **никто** | пишется `question.done`; используется только для наблюдаемости в админке | — |
| `rag.dead`, `rag.index.dead`, `rag.cron.dead` | — | только чтение | DLQ, доступны через admin API (`read_dead`) | — |

`scheduler` ничего не потребляет: раз в `CRON_INTERVAL_SECONDS` (по умолчанию 3600)
публикует задачу в `rag.cron`.

Общий цикл чтения — `application/consumer.py::consume_loop`:

- `ensure_group` → `XREADGROUP` (`count=1`, `block=STREAM_BLOCK_MS`);
- если новых сообщений нет — `XAUTOCLAIM` для pending с `idle > CONSUMER_PENDING_IDLE_MS` (60 c);
- ошибки чтения логируются, пауза 1 c;
- handler сам отвечает за `XACK` и DLQ.

Обработка ошибок в `worker`:

1. инкремент `jobs.attempts`;
2. если `attempts >= JOB_MAX_ATTEMPTS` (3) → `jobs.mark_failed` + `move_to_dead` + `XACK`;
3. иначе → `XACK` + повторный `XADD` в ту же очередь (ретрай).

Админка (`entrypoints/api/routers/admin.py`) показывает `stream_stats`
(length/pending/lag/consumers) и содержимое DLQ для всех трех очередей,
а также liveness воркеров (наличие консьюмеров в группе).

## 6. Асинхронные задачи

| Задача | Где выполняется | Триггер | Состояние |
|---|---|---|---|
| Ответ ассистента / подбор курса | `worker` | `POST /api/v1/chat/sessions/{id}/ask` | таблица `jobs`: `queued → running → done/failed` |
| Переиндексация описания курса | `indexer` | CRUD курса в кабинете преподавателя | запись в `content_chunks`/`chunk_embeddings` |
| Переиндексация шага | `indexer` | CRUD шага | то же (`step_upsert`) |
| `purge_terminal_jobs` | `cron` | `scheduler`, интервал `CRON_INTERVAL_SECONDS` | удаление `done`/`failed` старше `JOB_RETENTION_DAYS` (7) |

Жизненный цикл job-а:

```
POST /ask → jobs(queued) + XADD rag.requests → 202 {job_id}
worker: XREADGROUP → jobs.mark_running() (атомарный claim)
        → rewrite → embed → pgvector → GigaChat
        → одна транзакция: chat_messages + jobs(done) → XACK
        → XADD rag.events {event: question.done}
ошибка → attempts++ → (retry | rag.dead + jobs.failed)
GET /api/v1/jobs/{job_id} → queued | running | done | failed
```

Внутри процессов — обычный `asyncio`; graceful shutdown по `SIGINT`/`SIGTERM`
через `asyncio.Event`. Долгих CPU-bound задач нет, все I/O-bound.

## 7. Флоу ассистента (RAG-ответ)

Роутер: `entrypoints/api/routers/jobs.py`; обработчик:
`application/handlers.py::Handlers.send_question` / `process_question`.

1. **Постановка.** Проверяется доступ к сессии (владелец или `admin`), создается
   `jobs(queued)`, публикуется `{job_id, session_id, question}` в `rag.requests`,
   в job пишется `message_id` = id записи в Streams. Ответ — `202 {job_id}`.
2. **Захват задачи.** Воркер вызывает `ProcessQuestion`. `jobs.mark_running()`
   атомарно переводит `queued → running`; если не удалось (уже забрал другой
   воркер) — возвращается пустой ответ, сообщение все равно `XACK`-ается.
3. **Подготовка.**
   - история: `uow.chat.get_history(session_id, limit=10)`;
   - `rewrite_question` — LLM (temperature 0) переформулирует вопрос с учетом
     истории; при пустой истории вопрос возвращается как есть;
   - вопрос пользователя сохраняется в `chat_messages` (role=`user`).
4. **Развилка.** Если сессия **не** привязана к курсу и вопрос похож на просьбу
   подобрать курс (`looks_like_course_query`) → ветка рекомендаций (раздел 10).
5. **RAG.**
   - embedding переформулированного вопроса через Ollama;
   - поиск чанков (раздел 9);
   - если ничего не найдено → фиксированный ответ «Не удалось найти подходящие
     материалы.» (без вызова LLM);
   - иначе `build_context(chunks)` → system-промпт + `generate_answer`
     (temperature `LLM_TEMPERATURE`, по умолчанию 0.2).
6. **Постобработка.** `sanitize_course_recommendations` удаляет ссылки и пункты
   списка на курсы, которых нет среди найденных `course_id`; затем
   `normalize_answer_spacing`.
7. **Сохранение.** В одной транзакции: `chat_messages` (role=`assistant`,
   `sources`, `used_chunk_ids`) и `jobs(status=done, answer, sources,
   rewritten_question)`. Затем `XACK` и `XADD rag.events`.
8. **Получение результата.** `GET /api/v1/jobs/{job_id}` (проверка владения
   сессией). История и выгрузка диалога — `GET /api/v1/chat/sessions/{id}/messages`
   и `.../export?format=md|pdf`.

## 8. Как источники подаются в модель

Отдельного retrieval-сообщения нет: все складывается в **system-промпт**
(`domain/prompts.py`).

```
SYSTEM_PROMPT
  (правила: только переданные материалы, формат Markdown,
   обязательный блок «Источники:», правила для рекомендаций)
+ ТЕКУЩИЙ КУРС СТУДЕНТА        (если сессия привязана к курсу)
+ РЕКОМЕНДУЕМЫЕ КУРСЫ          (если ветка рекомендаций)
+ МАТЕРИАЛЫ КУРСА: build_context(chunks)
```

`build_context` (`domain/context.py`) для каждого чанка:

```
[Источник 1]
Курс: «Название» (/courses/ID)
Урок: <название урока или "Без названия">
Тип: theory | task
Материал:
<текст чанка>
```

Далее сообщения: история (`user`/`assistant`, `system` отфильтровывается) и
текущий вопрос как `user`.

Важно:

- модели **не** передаются `distance`/score и `chunk_id` — только текст, название
  курса, URL курса и тип источника;
- блок «Источники:» модель формирует сама в рамках ответа, бэкенд его только
  санитайзит;
- структурированные источники (`chunk_id`, `source_type`, `lesson`, `distance`,
  `course_id`, `course_title`, `course_url`) сохраняются в
  `chat_messages.sources` / `jobs.sources` и отдаются клиенту, но не модели.

## 9. Релевантность и отбор источников

### Чанки (RAG)

`adapters/persistence/repositories.py::SqlCourseChunkRepository.search`:

- метрика — cosine distance pgvector (`embedding <=> vector`), сортировка по
  возрастанию;
- фильтры: `model_name = EMBEDDING_MODEL`, `source_type IN ('theory','task')`,
  опционально `course_id = <курс сессии>`;
- отбор — просто `LIMIT RETRIEVAL_TOP_K` (по умолчанию 5);
- индекс `idx_embeddings_hnsw` (HNSW, `vector_cosine_ops`);
- `course_description` в RAG намеренно исключен.

Порога по score, реранкера, MMR и дедупликации по урокам нет.

### Курсы (рекомендации)

`SqlCourseRecommender.similar_courses`:

- по `chunk_embeddings` c `source_type = 'course_description'`;
- `MIN(distance)` по каждому курсу, `score = 1 - distance`;
- только `courses.is_published = true`;
- исключаются завершенные пользователем курсы;
- `ORDER BY best_distance LIMIT candidate_limit`, где
  `candidate_limit = max(RECOMMENDATION_TOP_K * 4, 20)`.

`domain/recommender.py::select_courses`:

```
threshold = max(RECOMMENDATION_MIN_SCORE, best_score - RECOMMENDATION_MARGIN)
оставить score >= threshold, затем взять первые RECOMMENDATION_TOP_K
```

Значения по умолчанию: `top_k=5`, `margin=0.05`, `min_score=0.0`.

Поисковый текст для эмбеддинга (`application/recommendations.py`) — конкатенация:

```
вопрос + LLM-расширение (до 15 ключевых слов, temperature 0)
       + профиль (interests, goals, preferred_level)
       + пройденные курсы (название + описание)
```

То есть профиль вклеивается в эмбеддинг запроса; отдельного вектора профиля нет
и в БД он не хранится.

## 10. Флоу рекомендаций курсов

Триггер — **только чат**: глобальная сессия (`course_id IS NULL`) и regex-интент
«какой курс», «курсы по», «посоветуй», «порекомендуй», «подбери курс»,
«с чего начать», «есть ли курс» (`domain/recommender.py`).

1. `rank_courses(...)` — отбор кандидатов (раздел 9).
2. Если кандидаты есть:
   - `build_recommended_courses_section` формирует секцию
     `- [«Название»](/courses/ID) — краткое описание`
     (описание обрезается до `RECOMMENDATION_DESCRIPTION_LIMIT`, 120 символов);
   - `generate_answer(context="", recommended_courses=...)` — LLM пишет ответ
     только по этой секции; system-промпт запрещает упоминать другие курсы и
     требует маркированный список;
   - `sanitize_course_recommendations` вырезает ссылки и пункты на курсы вне
     выборки и нормализует нумерацию в дефисы;
   - сохраняется `chat_messages.sources` с `source_type: "course_recommendation"`
     (`course_id`, `course_title`, `course_url`, `score`), `used_chunk_ids = []`;
     job помечается `done`.
3. Если кандидатов нет — падение в обычный RAG (поиск по всем курсам).

Отдельного списка «рекомендации для вас» в UI **нет**. На `/my-courses` есть
только форма «Обо мне» (`GET/PATCH /api/v1/preferences/me`), и эти поля
используются исключительно в чате.

## 11. Индексация контента

`adapters/persistence/course_indexer.py::CourseDescriptionIndexer`:

- `index(course_id)` — чанки `course_description` из `title + description`:
  текст очищается от HTML, режется на чанки по 500 слов с перекрытием 50;
  чанки и embeddings обновляются идемпотентно, устаревшие удаляются.
- `index_step(step_id)` — перестраивает чанки одного шага из его `step_contents`:
  `source_type = 'theory'` для `text`/`video`, иначе `task`. Перед вставкой
  удаляются старые чанки и их embeddings.

Очередь наполняется из кабинета преподавателя после CRUD
(`_enqueue_course_index` / `_enqueue_step_index`, `routers/teacher.py`):
`eventual consistency` — RAG-ответ может отставать от правки на время обработки
очереди. Массовая индексация — скрипт `scripts/embed_chunks.py`.

## 12. Конфигурация

`backend/src/courses_assistant/config.py` (pydantic-settings, `.env`):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/edu_platform_kurses` | БД |
| `REDIS_URL` | `redis://localhost:6379/0` | Streams |
| `GIGACHAT_CREDENTIALS` | — (обязательна для api/worker) | OAuth GigaChat |
| `GIGACHAT_BASE_URL` | `https://api.giga.chat/v1` | JSON API (не `giga.chat/v1`) |
| `GIGACHAT_MODEL` | `GigaChat-2` | модель |
| `OLLAMA_URL` | `http://localhost:11434/api/embed` | embeddings |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSION` | `nomic-embed-text` / `768` | модель и размерность |
| `RETRIEVAL_TOP_K` | `5` | сколько чанков отдавать в контекст |
| `RECOMMENDATION_TOP_K` / `_MARGIN` / `_MIN_SCORE` / `_DESCRIPTION_LIMIT` | `5` / `0.05` / `0.0` / `120` | подбор курсов |
| `STREAM_REQUESTS` / `STREAM_DEAD` / `STREAM_EVENTS` | `rag.requests` / `rag.dead` / `rag.events` | очереди чата |
| `STREAM_INDEX` / `INDEX_DLQ` | `rag.index.requests` / `rag.index.dead` | индексация |
| `STREAM_CRON` / `CRON_DLQ` | `rag.cron` / `rag.cron.dead` | cron |
| `CONSUMER_GROUP` / `CONSUMER_NAME` | `rag-workers` / `worker-1` | группа и имя консьюмера |
| `JOB_MAX_ATTEMPTS` | `3` | ретраи job-а |
| `CONSUMER_PENDING_IDLE_MS` | `60000` | порог `XAUTOCLAIM` |
| `STREAM_BLOCK_MS` | `5000` | блокирующее чтение (не задавать socket_timeout!) |
| `CRON_INTERVAL_SECONDS` | `3600` | период scheduler |
| `JOB_RETENTION_DAYS` | `7` | ретенция завершенных job-ов |
| `REDIS_STREAM_MAXLEN` / `_EVENTS_MAXLEN` | `10000` / `1000` | approximate-trim |
| `JWT_SECRET` / `JWT_ALGORITHM` | — (эфемерный) / `HS256` | подпись access |
| `ACCESS_TOKEN_TTL` / `REFRESH_TOKEN_TTL` | `900` / `1209600` | TTL токенов |
| `PASSWORD_KEY` | — (обязательна для паролей) | ключ Fernet |
| `LLM_TEMPERATURE` / `LLM_TIMEOUT` | `0.2` / `120` | генерация |

Веб-сервис имеет свой набор (`web/src/courses_web/config.py`): `API_BASE_URL`,
`WEB_HOST`, `WEB_PORT`, `LOG_LEVEL` и имена cookie для авто-refresh.

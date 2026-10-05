## Why

The RAG course assistant is currently a set of synchronous scripts (`app/*`) with raw `psycopg` calls and `input()`-driven "tests". It has no API, no queue, no ORM/migrations and cannot be run or scaled as a service. We need a production-shaped service: an HTTP API that enqueues questions, asynchronous workers that process them, migrations over the existing PostgreSQL + pgvector data, and a reproducible Docker Compose environment.

## What Changes

- Refactor the codebase to a Clean Architecture layout (domain / application / adapters / entrypoints) following the cosmicpython pattern.
- Add a FastAPI HTTP API exposing chat sessions, message history, an asynchronous `ask` endpoint and job status polling.
- Introduce a message bus backed by Redis Streams (consumer groups, ack, pending reclaim, retry + dead-letter).
- Process RAG questions asynchronously in a separate worker process; persist job state in PostgreSQL.
- Replace raw `psycopg` SQL with SQLAlchemy 2.0 async + asyncpg, and introduce Alembic migrations covering the existing 14-table schema plus a new `jobs` table.
- Keep GigaChat as the answer/rewrite LLM, replacing the official SDK with a direct `httpx` client (async, OAuth token cache).
- Keep `nomic-embed-text` (768) embeddings via Ollama; the existing schema and dumped embeddings are reused unchanged.
- Manage the environment with `uv`; provide `docker-compose` (PostgreSQL + pgvector, Redis, Ollama, API, worker, migrations), unit/integration/API tests, and CI.
- Remove the legacy `app/` package and the root `test_*.py` scripts after parity.

## Capabilities

### New Capabilities
- `rag-chat`: chat sessions, message history, and course-scoped RAG question answering (query rewrite, retrieval, context building, GigaChat answer generation).
- `question-jobs`: asynchronous question processing behind a Redis Streams bus, with durable job state and status polling.
- `platform-health`: liveness/readiness endpoints, configuration, database migrations, and the runnable Docker Compose environment.

### Modified Capabilities
<!-- None: no existing OpenSpec specs to modify. -->

## Impact

- **Code**: new `src/courses_assistant/` package; legacy `app/` and root `test_*.py` removed.
- **APIs**: new HTTP API under `/api/v1` (sessions, messages, ask, jobs) plus `/health`.
- **Data**: existing `edu_platform_kurses` schema reused; new `jobs` table; optional HNSW index on `chunk_embeddings`.
- **Dependencies**: FastAPI, uvicorn, SQLAlchemy 2.0, asyncpg, Alembic, pgvector, redis, httpx, tenacity, pydantic-settings, structlog; dev: pytest, pytest-asyncio, respx, ruff, mypy.
- **Infrastructure**: Dockerfile, docker-compose, Alembic, GitHub Actions CI.

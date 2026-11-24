## Context

See `proposal.md` for motivation. Current state and constraints that shape the design:

- The RAG logic already exists in `app/rag/*`, `app/chat/*`, `app/embeddings/*`, `app/llm/*` but is synchronous, uses raw `psycopg` and module-level globals.
- PostgreSQL already contains 14 tables with pgvector `vector(768)` and 2669 `nomic-embed-text` embeddings (dumped in `tmp/edu_platform_kurses.sql`). `chat_messages` has **both** `sources jsonb` and `used_chunk_ids jsonb`.
- The GigaChat Python SDK is synchronous and must be replaced by a direct `httpx` client.
- The dump is plain SQL (pg_dump 18.6) containing schema and data.
- Target scope is the RAG assistant only; auth/roles and course management are out of scope.

## Goals / Non-Goals

**Goals:**
- Clear Clean Architecture boundaries with testable use cases independent of I/O.
- HTTP API + asynchronous worker sharing one codebase and one DI container.
- Durable job state; broker used only for transport.
- Reuse existing schema, embeddings, and demo data without re-embedding.
- One-command reproducible environment and automated quality gates.

**Non-Goals:**
- Authentication, authorization, roles (deferred).
- Course authoring, adaptive task selection, progress analytics (deferred).
- Streaming/WebSocket answers; polling is sufficient.
- Changing the embedding model or re-embedding the corpus.

## Decisions

### D1. Layer boundaries (cosmicpython)
`domain` holds pure entities/value objects/prompt+context builders and domain errors. `application` holds commands/queries, handlers, ports (ABCs) and the in-process message bus. `adapters` implement ports (SQLAlchemy repos, GigaChat, Ollama, Redis Streams). `entrypoints` wire FastAPI and the worker.
- **Why:** dependency inversion; use cases are unit-testable with fakes.
- **Alternative:** keep the existing 3-module layout — rejected: untestable and no boundary.

### D2. Async SQLAlchemy 2.0 + asyncpg + Alembic
ORM maps all 14 existing tables plus `jobs`; `pgvector.sqlalchemy.Vector(768)` for embeddings; similarity via `embedding.cosine_distance(...)`; repository per aggregate behind a `UnitOfWork`.
- **Why:** async-native, typed, Alembic autogeneration, pgvector support.
- **Alternative:** raw `psycopg` + hand-written migrations — rejected: no metadata, more error-prone.

### D3. Redis Streams as the message bus
Stream `rag.requests`, consumer group `rag-workers`, `XACK` after terminal state, `XAUTOCLAIM` for pending, retry with attempt count, dead-letter stream `rag.dead`.
- **Why:** durable consumer groups, at-least-once delivery, no extra broker beyond Redis.
- **Alternative:** RabbitMQ — more infra; Celery — less control, heavier.

### D4. Job state in PostgreSQL, queue in Redis
New `jobs` table (`id`, `session_id`, `status`, `question`, `answer`, `sources`, `rewritten_question`, `error`, `attempts`, timestamps, `message_id`). The worker commits the assistant message and the terminal job state in one transaction.
- **Why:** durability and transactional consistency; survives Redis flush.
- **Alternative:** Redis-only hash+TTL — rejected: volatile results and non-atomic with message persistence.

### D5. GigaChat over httpx
`GigaChatLLM` performs OAuth2 client-credentials (`GIGACHAT_AUTH_URL`, `RqUID`, Basic credentials, form scope), caches the token until near `expires_at`, and calls `POST {GIGACHAT_BASE_URL}/chat/completions`. A single `httpx.AsyncClient` per process; re-auth once on `401`; `tenacity` backoff on `429/5xx`; `verify` configurable (default off).
- **Why:** async, no SDK coupling, explicit token lifecycle.
- **Alternative:** official SDK in a thread — rejected by request.

### D6. Embeddings unchanged (Ollama, `nomic-embed-text`, 768)
Adapter uses `httpx.AsyncClient` against `OLLAMA_URL`; `EMBEDDING_DIMENSION` validated fail-fast. Existing `chunk_embeddings` reused; no migration of vector dimension.
- **Why:** zero re-embedding, dump reusable as-is, fully free.

### D7. Demo data via init + stamp
`docker/postgres/init/edu_platform_kurses.sql` seeds schema+data on first Postgres start; a `migrate` step runs `alembic stamp <baseline>` then `alembic upgrade head` for future revisions.
- **Why:** preserves existing data and lets Alembic own schema evolution going forward.
- **Alternative:** strip data from the dump and load via a script — more fragile with a plain dump.

### D8. Tooling: uv, ruff, mypy, pytest, GitHub Actions
`pyproject.toml` with `uv`; ruff (lint+format), mypy, pytest with unit/integration/api markers. CI runs on GitHub (`yurzla/platforma_kurses`) with Postgres and Redis services and builds the Docker image.

## Risks / Trade-offs

- [GigaChat OAuth/endpoint details differ per deployment] → settings-driven URLs/scope, contract test with `respx`, one retry on 401.
- [Plain pg_dump 18.6 uses `\restrict`, unsupported by older `psql`] → run init with a Postgres 18 client or sanitize the dump before use.
- [Ollama in Compose is CPU-bound on macOS] → only 1 embedding per request at runtime; demo data already embedded.
- [At-least-once delivery may duplicate] → handler is idempotent via job state check and single terminal transaction.
- [Cross-process DI duplication between API and worker] → shared `container.py` factory.

## Migration Plan

1. Add the new package and tooling alongside `app/`; `app/` keeps working until parity.
2. Implement layers and adapters; cover with unit/integration tests.
3. Add Alembic baseline + `jobs`; validate on a scratch database.
4. Wire API and worker; verify the 202→poll→done flow.
5. Add Compose; verify cold start with the dump.
6. Remove `app/` and root `test_*.py`; run full CI.
Rollback: revert to the `Refac-architecture` branch state; the database is additive (only `jobs` is new), so no destructive migration is required.

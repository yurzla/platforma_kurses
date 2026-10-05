## 1. Bootstrap

- [x] 1.1 Create `pyproject.toml` with `uv`-managed runtime/dev dependencies and `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`; verify `uv sync` succeeds
- [x] 1.2 Add `.python-version`, `.env.example`, `Makefile` (`install/lint/typecheck/test/migrate/up/down`) and `src/courses_assistant/__init__.py`; verify `make lint` runs
- [x] 1.3 Implement `config.py` with pydantic-settings (DSN, REDIS_URL, GigaChat, Ollama, embedding dimension) and fail-fast validation; verify with a unit test for a missing required secret

## 2. Domain and application

- [x] 2.1 Implement domain models/value objects/errors (`ChatSession`, `ChatMessage`, `ContentChunk`, `RetrievedChunk`, `Answer`, `Role`, `SourceType`) with unit tests
- [x] 2.2 Move prompt/context building into domain (`prompts.py`, `context.py`) with unit tests covering context formatting
- [x] 2.3 Define application ports (ABCs): `ChatRepository`, `CourseChunkRepository`, `JobRepository`, `UnitOfWork`, `LLM`, `Embedder`, `MessageBroker`; verify imports and abstract contracts
- [x] 2.4 Implement `message_bus.py`, command/event types and handlers (`CreateChatSession`, `SendQuestion`, `ProcessQuestion`) using only ports; unit-test handlers with in-memory fakes in `tests/fakes.py`
- [x] 2.5 Implement query handlers for history and job status; unit-test with fakes

## 3. Persistence

- [x] 3.1 Implement SQLAlchemy ORM mapping all 14 existing tables, including `chat_messages` with both `sources` and `used_chunk_ids`, and `chunk_embeddings.embedding = Vector(768)`
- [x] 3.2 Implement async engine/session factory and `SqlAlchemyUnitOfWork` with repository implementations; integration-test create session, save/read history against a test Postgres
- [x] 3.3 Implement cosine-distance retrieval restricted by `course_id` and `model_name`; integration-test ordering and course isolation
- [x] 3.4 Initialize Alembic and write the baseline migration reproducing the 14 tables plus the `jobs` table; verify `alembic upgrade head` on an empty database
- [x] 3.5 Add an optional HNSW index migration on `chunk_embeddings.embedding`; verify it applies and is idempotent

## 4. Adapters

- [x] 4.1 Implement `OllamaEmbedder` with async `httpx` and dimension validation; unit-test with `respx` (success and dimension mismatch)
- [x] 4.2 Implement `GigaChatLLM` over `httpx` (OAuth token cache, re-auth on 401, `tenacity` backoff, `verify` flag); unit-test with `respx` for token fetch, chat success, 401 re-auth and 429 backoff
- [x] 4.3 Implement `RedisStreamsBroker` (publish, consumer group, ack, `XAUTOCLAIM`, retry, dead-letter); integration-test publish/consume/ack and pending reclaim against Redis

## 5. Entrypoints

- [x] 5.1 Implement FastAPI app factory, DI `container`, request-id middleware and structured logging; verify app starts in tests
- [x] 5.2 Implement routers `chat` (create session, history), `jobs` (`POST ask` -> 202, `GET /jobs/{id}`) and `health`/`ready`; API-test the full 202 -> poll -> done flow and 404/422 cases with fakes
- [x] 5.3 Implement the worker entrypoint consuming `rag.requests`, running `ProcessQuestion`, committing terminal state transactionally, and handling graceful shutdown

## 6. Infrastructure

- [x] 6.1 Write `Dockerfile` and `docker-compose.yml` (Postgres+pgvector, Redis, Ollama + model pull, `migrate`, `api`, `worker`) with healthchecks and startup ordering
- [x] 6.2 Add `docker/postgres/init/edu_platform_kurses.sql` and the migrate/stamp step; verify cold start loads schema+demo data and the API health endpoint responds
- [x] 6.3 Write `README.md` with architecture diagram, run instructions and API overview

## 7. Tooling, CI and cleanup

- [x] 7.1 Port `stepik_dump`, `load_stepik`, `embed_chunks` into `src/courses_assistant/scripts` as CLI commands using the new config; verify `--help` works
- [x] 7.2 Add GitHub Actions workflow: uv sync, `ruff`, `mypy`, `pytest` with Postgres/Redis services, and `docker build`
- [x] 7.3 Remove the legacy `app/` package and root `test_*.py`; verify the full test suite, lint and typecheck pass

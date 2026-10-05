# platform-health

## Purpose

Makes the service operable and reproducible: health/readiness reporting, environment configuration, database migrations over the existing course schema, and a Docker Compose runtime that starts the whole system from a clean checkout.

## Requirements

### Requirement: Health and readiness
The system SHALL expose a liveness endpoint that always reports the process as alive and a readiness endpoint that reports whether required dependencies (PostgreSQL and Redis) are reachable.

#### Scenario: Liveness
- **WHEN** a client calls the liveness endpoint
- **THEN** the system responds with HTTP 200 regardless of dependency state

#### Scenario: Readiness OK
- **WHEN** PostgreSQL and Redis are reachable
- **THEN** the readiness endpoint responds with HTTP 200

#### Scenario: Readiness degraded
- **WHEN** PostgreSQL or Redis is unreachable
- **THEN** the readiness endpoint responds with HTTP 503 and identifies the unavailable dependency

### Requirement: Database migrations
The system SHALL manage the database schema with Alembic migrations that reproduce the existing 14-table course schema (including `chat_messages` with both `sources` and `used_chunk_ids`) and add the `jobs` table.

#### Scenario: Migrations applied to empty database
- **WHEN** `alembic upgrade head` runs against an empty database
- **THEN** the full schema, including the pgvector extension usage and the `jobs` table, is created

#### Scenario: Demo data loaded
- **WHEN** the compose environment starts with the provided dump for the first time
- **THEN** the schema and demo data are loaded and Alembic is stamped at the baseline revision

### Requirement: Containerized runtime
The system SHALL be startable with a single `docker compose up` command that runs PostgreSQL with pgvector, Redis, Ollama with the embedding model, the JSON API, an HTML web service, the worker, a scheduler that enqueues periodic maintenance tasks, and a cron consumer that executes them, with health-gated startup ordering. The backend services SHALL be built from a backend image and the web service from a separate web image whose dependency set excludes database, queue, and LLM libraries.

#### Scenario: Cold start
- **WHEN** a developer runs `docker compose up` on a clean checkout with a populated `.env`
- **THEN** migrations run, all services become healthy, and both the API and web health endpoints respond

#### Scenario: Maintenance services started
- **WHEN** the compose stack is up
- **THEN** the scheduler and cron services run alongside the API, web, and worker

#### Scenario: Web depends on API
- **WHEN** the compose stack starts
- **THEN** the web service waits for the API health check before starting

#### Scenario: Separate images
- **WHEN** the backend and web images are built
- **THEN** the web image contains only the web package and its runtime dependencies and does not include the database, queue, or LLM libraries

### Requirement: Runtime configuration from environment
The system SHALL read runtime configuration from environment variables with documented defaults for non-secret values. The backend SHALL read database, Redis, GigaChat, Ollama, session, and API settings. The web service SHALL read only its own settings (API base URL, host, port, and log level) and SHALL NOT require database, Redis, or LLM configuration to start.

#### Scenario: Missing required secret
- **WHEN** the backend starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Session settings configured
- **WHEN** the backend starts with session settings `SESSION_SECRET`, `COOKIE_SECURE`, and `SESSION_MAX_AGE`
- **THEN** the session cookie is signed with the configured secret and uses the configured security and lifetime settings

#### Scenario: Session secret missing
- **WHEN** no session secret is configured
- **THEN** the backend generates an ephemeral secret for the process and logs a warning

#### Scenario: Service endpoints configured
- **WHEN** the API and web services start
- **THEN** the API listens on `API_PORT` (default `5000`), the web service listens on `WEB_PORT` (default `8000`), and the web service reaches the API at `API_BASE_URL`

#### Scenario: Web configured independently
- **WHEN** the web service starts without any database, Redis, or LLM settings
- **THEN** it starts normally and serves pages and proxies requests to the API

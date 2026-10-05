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

### Requirement: Configuration from environment
The system SHALL read all runtime configuration (database DSN, Redis URL, GigaChat credentials and endpoints, Ollama URL and embedding model, admin login credentials and session secret) from environment variables with documented defaults for non-secret values.

#### Scenario: Missing required secret
- **WHEN** the application starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Admin credentials optional
- **WHEN** the admin username and password are not provided
- **THEN** the application starts normally and the dashboard/admin API remain open

### Requirement: Database migrations
The system SHALL manage the database schema with Alembic migrations that reproduce the existing 14-table course schema (including `chat_messages` with both `sources` and `used_chunk_ids`) and add the `jobs` table.

#### Scenario: Migrations applied to empty database
- **WHEN** `alembic upgrade head` runs against an empty database
- **THEN** the full schema, including the pgvector extension usage and the `jobs` table, is created

#### Scenario: Demo data loaded
- **WHEN** the compose environment starts with the provided dump for the first time
- **THEN** the schema and demo data are loaded and Alembic is stamped at the baseline revision

### Requirement: Containerized runtime
The system SHALL be startable with a single `docker compose up` command that runs PostgreSQL with pgvector, Redis, Ollama with the embedding model, the API, the worker, a scheduler that enqueues periodic maintenance tasks, and a cron consumer that executes them, with health-gated startup ordering.

#### Scenario: Cold start
- **WHEN** a developer runs `docker compose up` on a clean checkout with a populated `.env`
- **THEN** migrations run, all services become healthy, and the API responds on its health endpoint

#### Scenario: Maintenance services started
- **WHEN** the compose stack is up
- **THEN** the scheduler and cron services run alongside the API and worker

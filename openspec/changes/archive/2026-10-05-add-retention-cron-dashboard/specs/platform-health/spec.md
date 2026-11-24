## MODIFIED Requirements

### Requirement: Containerized runtime
The system SHALL be startable with a single `docker compose up` command that runs PostgreSQL with pgvector, Redis, Ollama with the embedding model, the API, the worker, a scheduler that enqueues periodic maintenance tasks, and a cron consumer that executes them, with health-gated startup ordering.

#### Scenario: Cold start
- **WHEN** a developer runs `docker compose up` on a clean checkout with a populated `.env`
- **THEN** migrations run, all services become healthy, and the API responds on its health endpoint

#### Scenario: Maintenance services started
- **WHEN** the compose stack is up
- **THEN** the scheduler and cron services run alongside the API and worker

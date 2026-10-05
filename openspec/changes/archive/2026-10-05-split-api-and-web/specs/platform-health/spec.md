## MODIFIED Requirements

### Requirement: Configuration from environment
The system SHALL read all runtime configuration (database DSN, Redis URL, GigaChat credentials and endpoints, Ollama URL and embedding model, admin login credentials and session secret, the API port, the web port, and the API base URL used by the web service) from environment variables with documented defaults for non-secret values.

#### Scenario: Missing required secret
- **WHEN** the application starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Admin credentials optional
- **WHEN** the admin username and password are not provided
- **THEN** the application starts normally and the admin API remains open

#### Scenario: Service endpoints configured
- **WHEN** the API and web services start
- **THEN** the API listens on `API_PORT` (default `5000`), the web service listens on `WEB_PORT` (default `8000`), and the web service reaches the API at `API_BASE_URL`

### Requirement: Containerized runtime
The system SHALL be startable with a single `docker compose up` command that runs PostgreSQL with pgvector, Redis, Ollama with the embedding model, the JSON API, an HTML web service, the worker, a scheduler that enqueues periodic maintenance tasks, and a cron consumer that executes them, with health-gated startup ordering.

#### Scenario: Cold start
- **WHEN** a developer runs `docker compose up` on a clean checkout with a populated `.env`
- **THEN** migrations run, all services become healthy, and both the API and web health endpoints respond

#### Scenario: Maintenance services started
- **WHEN** the compose stack is up
- **THEN** the scheduler and cron services run alongside the API, web, and worker

#### Scenario: Web depends on API
- **WHEN** the compose stack starts
- **THEN** the web service waits for the API health check before starting

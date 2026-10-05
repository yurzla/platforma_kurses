## MODIFIED Requirements

### Requirement: Configuration from environment
The system SHALL read runtime configuration from environment variables with documented defaults for non-secret values. The backend SHALL read database, Redis, GigaChat, Ollama, admin, and API settings. The web service SHALL read only its own settings (API base URL, host, port, and log level) and SHALL NOT require database, Redis, or LLM configuration to start.

#### Scenario: Missing required secret
- **WHEN** the backend starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Admin credentials optional
- **WHEN** the admin username and password are not provided
- **THEN** the application starts normally and the admin API remains open

#### Scenario: Service endpoints configured
- **WHEN** the API and web services start
- **THEN** the API listens on `API_PORT` (default `5000`), the web service listens on `WEB_PORT` (default `8000`), and the web service reaches the API at `API_BASE_URL`

#### Scenario: Web configured independently
- **WHEN** the web service starts without any database, Redis, or LLM settings
- **THEN** it starts normally and serves pages and proxies requests to the API

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

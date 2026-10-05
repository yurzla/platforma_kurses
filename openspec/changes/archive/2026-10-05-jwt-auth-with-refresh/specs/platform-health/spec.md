## MODIFIED Requirements

### Requirement: Runtime configuration from environment
The system SHALL read runtime configuration from environment variables with documented defaults for non-secret values. The backend SHALL read database, Redis, GigaChat, Ollama, JWT, and API settings. The web service SHALL read only its own settings (API base URL, host, port, and log level) and SHALL NOT require database, Redis, or LLM configuration to start.

#### Scenario: Missing required secret
- **WHEN** the backend starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Session settings configured
- **WHEN** the backend starts with JWT settings `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL`, and `COOKIE_SECURE`
- **THEN** access tokens are signed with the configured secret and algorithm, token lifetimes follow the configured TTLs, and cookies use the configured security setting

#### Scenario: Session secret missing
- **WHEN** no JWT secret is configured
- **THEN** the backend generates an ephemeral secret for the process and logs a warning

#### Scenario: Service endpoints configured
- **WHEN** the API and web services start
- **THEN** the API listens on `API_PORT` (default `5000`), the web service listens on `WEB_PORT` (default `8000`), and the web service reaches the API at `API_BASE_URL`

#### Scenario: Web configured independently
- **WHEN** the web service starts without any database, Redis, or LLM settings
- **THEN** it starts normally and serves pages and proxies requests to the API

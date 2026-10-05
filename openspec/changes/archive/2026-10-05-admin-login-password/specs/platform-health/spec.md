## MODIFIED Requirements

### Requirement: Configuration from environment
The system SHALL read all runtime configuration (database DSN, Redis URL, GigaChat credentials and endpoints, Ollama URL and embedding model, admin login credentials and session secret) from environment variables with documented defaults for non-secret values.

#### Scenario: Missing required secret
- **WHEN** the application starts without a required secret such as GigaChat credentials
- **THEN** startup fails with a clear error naming the missing setting

#### Scenario: Admin credentials optional
- **WHEN** the admin username and password are not provided
- **THEN** the application starts normally and the dashboard/admin API remain open

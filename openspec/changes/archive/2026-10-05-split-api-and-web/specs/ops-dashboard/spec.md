## MODIFIED Requirements

### Requirement: Dashboard page
The system SHALL serve a human-readable dashboard page from the web service presenting jobs, dead-letter entries, and stream metrics with automatic refresh, and SHALL provide a control to switch between light and dark themes.

#### Scenario: Dashboard rendered
- **WHEN** an authenticated admin requests the dashboard page
- **THEN** the web service returns an HTML page with sections for jobs, DLQ, and streams and the assets to refresh them

#### Scenario: Data retrieved through the API
- **WHEN** the dashboard page loads its data
- **THEN** the browser-issued requests are proxied by the web service to the JSON API

#### Scenario: Theme control present
- **WHEN** the dashboard page is served
- **THEN** it includes a theme toggle control

### Requirement: Admin login (username/password)
The system SHALL protect the admin API with a username and password when both are configured, and SHALL leave it open when no credentials are configured; the login form SHALL be served by the web service and SHALL authenticate against the JSON API.

#### Scenario: Login required and missing
- **WHEN** credentials are configured and a client calls the admin API without an authenticated session
- **THEN** the system responds with HTTP 401

#### Scenario: Successful login
- **WHEN** a client submits the correct username and password to the login form served by the web service
- **THEN** the API establishes an authenticated session and the web service serves the dashboard and admin API data

#### Scenario: Invalid credentials
- **WHEN** a client submits an incorrect username or password
- **THEN** the system responds with HTTP 401 and does not establish a session

#### Scenario: No credentials configured
- **WHEN** no admin username/password are configured
- **THEN** the admin API is accessible without login

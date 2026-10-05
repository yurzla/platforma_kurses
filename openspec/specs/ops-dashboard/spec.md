# ops-dashboard Specification

## Purpose
Read-only обзор для оператора: статусы асинхронных job-ов, содержимое dead-letter очередей и метрики Redis Streams, с опциональным ограничением доступа.

## Requirements

### Requirement: Job overview and listing
The system SHALL expose read-only endpoints that report job counts by status and a paginated, filterable list of jobs.

#### Scenario: Status counts
- **WHEN** a client requests the overview
- **THEN** the system returns the number of jobs in each status and stream metrics

#### Scenario: Filtered list
- **WHEN** a client requests the job list with a status, session, or text filter and pagination
- **THEN** the system returns the matching jobs (newest first) plus the total count

#### Scenario: Unknown status filter
- **WHEN** a client requests the job list with an unsupported status value
- **THEN** the system responds with HTTP 400

### Requirement: Dead-letter visibility
The system SHALL expose a read-only endpoint listing recent dead-letter entries from the relevant dead-letter streams.

#### Scenario: DLQ entries listed
- **WHEN** a client requests the DLQ listing
- **THEN** the system returns recent entries with their message id, originating stream, and error reason

### Requirement: Stream metrics
The system SHALL expose per-stream metrics including length and consumer-group pending/lag for the operational streams.

#### Scenario: Stream metrics returned
- **WHEN** a client requests stream metrics
- **THEN** the system returns, for each operational stream, its length and — where a consumer group is configured — pending, lag, and consumer count

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

### Requirement: Admin session and logout
The system SHALL keep the authenticated session in a signed, HttpOnly cookie and SHALL allow the operator to log out.

#### Scenario: Session persists
- **WHEN** a client logs in and then loads the dashboard or calls the admin API
- **THEN** the requests are served using the session cookie

#### Scenario: Logout
- **WHEN** an authenticated client calls the logout endpoint
- **THEN** the session is cleared and subsequent admin requests require login again

#### Scenario: HTML page without session
- **WHEN** an unauthenticated client requests the dashboard HTML page
- **THEN** the system redirects to the login page with a `next` parameter pointing back to the requested page

### Requirement: Theme switching
The system SHALL allow switching between light and dark themes on the dashboard and login pages, and SHALL remember the operator's choice.

#### Scenario: Toggle theme
- **WHEN** the operator activates the theme toggle
- **THEN** the interface switches between light and dark themes immediately

#### Scenario: Preference persists
- **WHEN** the operator has chosen a theme and reloads the page or opens another page of the interface
- **THEN** the previously chosen theme is applied without a flash of the other theme

#### Scenario: Default to system preference
- **WHEN** no theme has been chosen yet
- **THEN** the initial theme follows the operating system's color-scheme preference

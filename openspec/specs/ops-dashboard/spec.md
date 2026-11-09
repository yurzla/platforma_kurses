# ops-dashboard Specification

## Purpose
Read-only обзор для оператора: статусы асинхронных job-ов, содержимое dead-letter очередей, метрики Redis Streams, детали источников ответа, чанки и эмбеддинги RAG-индекса и состояние зависимостей, с ограничением доступа по роли администратора.

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

### Requirement: Admin authorization by role
The system SHALL protect the admin API and the admin page so that they are accessible only to authenticated users whose role is `admin`.

#### Scenario: Admin access granted
- **WHEN** an authenticated user with role `admin` calls the admin API or requests the admin page
- **THEN** the system returns the requested data or page

#### Scenario: Non-admin access denied
- **WHEN** an authenticated user whose role is not `admin` calls the admin API
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous access denied
- **WHEN** an unauthenticated client calls the admin API
- **THEN** the system responds with HTTP 401

#### Scenario: Role change takes effect
- **WHEN** a user's role is changed to `admin` or away from it
- **THEN** subsequent admin requests are authorized according to the current role

### Requirement: Job inspection
The system SHALL expose the existing read-only job details endpoint and SHALL present the full question, answer, rewritten question, error, attempts, timestamps, and retrieved sources to an administrator without changing the job.

#### Scenario: Job details opened
- **WHEN** an administrator selects a job in the dashboard
- **THEN** the dashboard shows its full question, answer, error, attempts, timestamps, and the list of retrieved sources

#### Scenario: Source metadata shown
- **WHEN** job details contain retrieved sources
- **THEN** each source shows its chunk id, course, lesson, source type, and distance

#### Scenario: Job details do not mutate the job
- **WHEN** an administrator opens job details
- **THEN** the job status, attempts, and queue state remain unchanged

### Requirement: Chunk inspection
The system SHALL expose read-only endpoints to list content chunks with filters and to return a single chunk with its text and embedding metadata.

#### Scenario: Chunk list filtered
- **WHEN** an administrator requests the chunk list with a course, source type, or text filter and pagination
- **THEN** the system returns the matching chunks with course, lesson, type, short text, and whether an embedding exists, plus the total count

#### Scenario: Chunk detail returned
- **WHEN** an administrator requests an existing chunk by id
- **THEN** the system returns its full text, metadata, and embedding model and dimension when an embedding exists

#### Scenario: Unknown chunk
- **WHEN** an administrator requests a chunk id that does not exist
- **THEN** the system responds with HTTP 404

### Requirement: RAG index summary
The system SHALL expose a read-only summary of the retrieval index covering chunk and embedding counts, chunks without embeddings, distribution by source type and course, and the embedding model, dimension, and latest embedding time.

#### Scenario: Index summary returned
- **WHEN** an administrator requests the index summary
- **THEN** the system returns totals for chunks and embeddings, the number of chunks without an embedding, the per-type and per-course breakdown, and the configured model and dimension

#### Scenario: Empty index
- **WHEN** the database contains no chunks
- **THEN** the system returns zero counts and empty breakdowns without an error

### Requirement: Dependency state summary
The system SHALL expose a read-only health summary for administrators covering PostgreSQL, Redis, Ollama availability with the configured embedding model, the latest done and failed job times, the oldest queued job time, and the active retrieval settings.

#### Scenario: Dependencies checked
- **WHEN** an administrator requests the health summary
- **THEN** the system reports the state of PostgreSQL, Redis, and Ollama and whether the configured embedding model is available

#### Scenario: Job timestamps reported
- **WHEN** an administrator requests the health summary
- **THEN** the system reports the latest done and failed job times and the oldest queued job time when such jobs exist

#### Scenario: Dependency unavailable
- **WHEN** a dependency cannot be reached
- **THEN** the system reports it as unavailable without failing the request

### Requirement: Diagnostics access control
The system SHALL restrict the job inspection, chunk inspection, index summary, and dependency state endpoints to authenticated users with the `admin` role.

#### Scenario: Administrator allowed
- **WHEN** an authenticated administrator calls a diagnostics endpoint
- **THEN** the system returns the requested diagnostic data

#### Scenario: Non-administrator denied
- **WHEN** an authenticated user without the `admin` role calls a diagnostics endpoint
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous denied
- **WHEN** an unauthenticated client calls a diagnostics endpoint
- **THEN** the system responds with HTTP 401

### Requirement: Recommendation sources in job details
The system SHALL display recommendation sources separately from chunk sources in job details.

#### Scenario: Recommended courses shown
- **WHEN** an administrator opens a job whose sources are course recommendations
- **THEN** the dashboard lists the recommended courses with links and relevance scores

#### Scenario: Chunk sources unchanged
- **WHEN** job details contain chunk sources
- **THEN** the dashboard continues to show chunk id, course, lesson, source type, and distance

#### Scenario: Empty sources message
- **WHEN** job details contain neither chunk nor recommendation sources
- **THEN** the dashboard reports that sources were not saved

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

### Requirement: Optional admin access token
The system SHALL allow protecting the dashboard and admin API with a configured token, while remaining open when no token is configured.

#### Scenario: Token configured and missing
- **WHEN** an admin token is configured and a client calls the dashboard or admin API without a valid token
- **THEN** the system responds with HTTP 401

#### Scenario: Token supplied
- **WHEN** an admin token is configured and the client supplies it via Authorization header, cookie, or query parameter
- **THEN** the request is served

#### Scenario: No token configured
- **WHEN** no admin token is configured
- **THEN** the dashboard and admin API are accessible without a token

### Requirement: Dashboard page
The system SHALL serve a human-readable dashboard page presenting jobs, dead-letter entries, and stream metrics with automatic refresh.

#### Scenario: Dashboard rendered
- **WHEN** a client requests the dashboard page
- **THEN** the system returns an HTML page with sections for jobs, DLQ, and streams and the assets to refresh them

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

The system SHALL expose a read-only endpoint listing recent dead-letter entries from every
configured dead-letter stream (chat requests, course/step indexing, and cron), including for each
entry its message id, the originating queue, the dead-letter stream it was read from, and the error
reason, and SHALL allow filtering the listing by dead-letter stream without failing when a
dead-letter stream does not exist yet.

#### Scenario: DLQ entries listed

- **WHEN** a client requests the DLQ listing
- **THEN** the system returns recent entries from all configured dead-letter streams, each with its
  message id, originating queue, dead-letter stream, and error reason

#### Scenario: Indexing failure visible

- **WHEN** an indexing message could not be processed and was moved to its dead-letter stream
- **THEN** the DLQ listing includes that entry and identifies its dead-letter stream as the indexing
  dead-letter stream

#### Scenario: Filter by dead-letter stream

- **WHEN** a client requests the DLQ listing filtered by a specific dead-letter stream
- **THEN** the system returns only entries read from that dead-letter stream

#### Scenario: Empty dead-letter stream

- **WHEN** a configured dead-letter stream has no entries or does not exist
- **THEN** the listing still returns entries from the other dead-letter streams without an error

### Requirement: Stream metrics

The system SHALL expose per-stream metrics for all operational streams and dead-letter streams,
including whether the stream exists, its length, the id and timestamp of its newest message, and —
where a consumer group is configured — its pending and lag counters, consumer count, and the
per-consumer pending and idle time.

#### Scenario: Stream metrics returned

- **WHEN** a client requests stream metrics
- **THEN** the system returns, for each operational stream, its length and — where a consumer group
  is configured — pending, lag, and consumer count together with the newest message id and time

#### Scenario: Consumer detail returned

- **WHEN** a consumer group has registered consumers
- **THEN** the metrics include each consumer's name, pending count, and idle time

#### Scenario: Stream does not exist

- **WHEN** a configured stream has not been created yet
- **THEN** the metrics report it as non-existent with zero length and without failing the request

#### Scenario: Dead-letter streams distinguished

- **WHEN** the client requests stream metrics
- **THEN** each stream is marked as either an operational queue or a dead-letter stream

### Requirement: Dashboard page

The system SHALL serve a human-readable dashboard page from the web service presenting jobs,
dead-letter entries, stream metrics, index summary, chunks, and dependency state with automatic
refresh, and SHALL provide a control to switch between light and dark themes. The dead-letter
section SHALL let the operator see and filter the dead-letter stream, the streams section SHALL show
the newest message time and consumer detail with visual highlighting of pending or lagging queues,
the index section SHALL show the indexing queue state, and the dependency section SHALL show worker
liveness.

#### Scenario: Dashboard rendered

- **WHEN** an authenticated admin requests the dashboard page
- **THEN** the web service returns an HTML page with sections for jobs, DLQ, streams, index, chunks,
  and dependency state and the assets to refresh them

#### Scenario: Data retrieved through the API

- **WHEN** the dashboard page loads its data
- **THEN** the browser-issued requests are proxied by the web service to the JSON API

#### Scenario: Theme control present

- **WHEN** the dashboard page is served
- **THEN** it includes a theme toggle control

#### Scenario: Dead-letter stream visible and filterable

- **WHEN** an administrator opens the DLQ sub-tab
- **THEN** the entries show their dead-letter stream and a control filters entries by that stream

#### Scenario: Stream backlog highlighted

- **WHEN** a stream has pending messages or positive lag
- **THEN** the streams sub-tab visually highlights that row

#### Scenario: Index queue shown

- **WHEN** an administrator opens the index sub-tab
- **THEN** it shows the indexing queue length, pending, lag, and the number of indexing dead-letter
  entries

#### Scenario: Worker liveness shown

- **WHEN** an administrator opens the dependency state sub-tab
- **THEN** it shows whether each worker consumer group has live consumers

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
The system SHALL expose a read-only summary of the retrieval index covering chunk and embedding counts, chunks without embeddings, every course's chunk and embedding coverage, the number of courses without embeddings or chunks, and the embedding model, dimension, and latest embedding time.

#### Scenario: Index summary returned
- **WHEN** an administrator requests the index summary
- **THEN** the system returns totals for chunks and embeddings, the number of chunks without an embedding, the number of courses without embeddings and without chunks, the per-type and per-course breakdown, and the configured model and dimension

#### Scenario: Empty index
- **WHEN** the database contains no chunks
- **THEN** the system returns zero counts and empty breakdowns without an error

#### Scenario: Courses without chunks listed
- **WHEN** a course has no content chunks
- **THEN** the per-course breakdown includes it with zero counts and an empty status

#### Scenario: Course embedding coverage
- **WHEN** a course has chunks but no embeddings or only some embeddings
- **THEN** the per-course breakdown reports the missing or partial embedding status

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

### Requirement: Chunk inspection tab
The dashboard SHALL present chunk filtering and chunk listing in a dedicated diagnostics sub-tab separate from the index summary.

#### Scenario: Chunks tab opened
- **WHEN** an administrator opens the chunks sub-tab
- **THEN** the dashboard shows the chunk filters, chunk table, and pagination

#### Scenario: Index summary remains separate
- **WHEN** an administrator opens the index sub-tab
- **THEN** it shows the index totals, source-type breakdown, and per-course coverage without the chunk list

#### Scenario: Course filter available
- **WHEN** an administrator opens the chunks sub-tab without opening the index sub-tab first
- **THEN** the course filter is populated from the index summary

### Requirement: Filter toolbar layout
The dashboard SHALL render the Jobs and chunks filter panels as a single-row toolbar with equal-height controls and right-aligned actions, and SHALL truncate long course titles in the course filter.

#### Scenario: Jobs filters in one row
- **WHEN** an administrator opens the Jobs sub-tab
- **THEN** the status, session, and search fields stay on one row with the apply and reset buttons aligned to the right

#### Scenario: Chunks filters in one row
- **WHEN** an administrator opens the chunks sub-tab
- **THEN** the course, source type, and search fields stay on one row with the apply and reset buttons aligned to the right

#### Scenario: Equal control height
- **WHEN** a filter toolbar is rendered
- **THEN** inputs, selects, and buttons share the same height

#### Scenario: Long course title truncated
- **WHEN** a course title does not fit the course filter
- **THEN** the title is truncated with an ellipsis instead of widening the toolbar

### Requirement: Course filter selection persistence
The dashboard SHALL keep the currently selected course filter value across background index refreshes until the administrator applies or resets the filter.

#### Scenario: Selection survives background refresh
- **WHEN** an administrator selects a course in the chunks course filter and waits for the periodic refresh
- **THEN** the selected course remains selected

#### Scenario: Options rebuilt only on change
- **WHEN** the periodic refresh returns the same course list
- **THEN** the course filter options are not rebuilt and the open selection is not disturbed

#### Scenario: Applied filter preserved
- **WHEN** an administrator applies a course filter and the refresh runs later
- **THEN** the applied course stays selected and the filtered chunk list remains consistent with the selection

### Requirement: Job status cards scope
The dashboard SHALL show the job status summary cards only on the Jobs sub-tab.

#### Scenario: Cards visible on Jobs
- **WHEN** an administrator opens the Jobs sub-tab
- **THEN** the queued, running, done, and failed cards are visible

#### Scenario: Cards hidden on other sub-tabs
- **WHEN** an administrator opens the DLQ, Streams, index, chunks, or health sub-tab
- **THEN** the job status cards are not shown

#### Scenario: Card click filters jobs
- **WHEN** an administrator clicks a job status card
- **THEN** the dashboard opens the Jobs sub-tab with that status applied to the filter

### Requirement: Indexing queue observability

The system SHALL report the state of the course and step indexing queue, including its length,
pending messages, consumer lag, and the number of dead-letter entries produced by indexing, so an
administrator can detect stalled or failing indexing.

#### Scenario: Index queue reported

- **WHEN** an administrator requests the index summary
- **THEN** the system returns the indexing queue length and consumer-group pending and lag

#### Scenario: Indexing dead letters counted

- **WHEN** the indexing dead-letter stream contains entries
- **THEN** the index summary reports their count

#### Scenario: Indexing queue idle

- **WHEN** the indexing queue is empty and no consumers have pending messages
- **THEN** the index summary reports zero queue values without an error

### Requirement: Worker liveness in health summary

The system SHALL report, in the administrator health summary, whether each background consumer group
has registered consumers, covering chat workers, indexers, and cron workers.

#### Scenario: Consumers registered

- **WHEN** an administrator requests the health summary
- **THEN** it reports the consumer count for each background worker group and marks a group with
  consumers as available

#### Scenario: Worker group without consumers

- **WHEN** a background worker group has no registered consumers
- **THEN** the health summary marks that group as unavailable without failing the request

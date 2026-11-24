## MODIFIED Requirements

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

## ADDED Requirements

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

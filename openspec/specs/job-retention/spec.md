# job-retention Specification

## Purpose
Ограничивает рост служебных данных: стримы Redis и таблица `jobs` не должны расти бесконечно на долгой эксплуатации.

## Requirements

### Requirement: Bounded Redis streams
The system SHALL bound the size of Redis Streams by trimming entries as they are published, using per-stream limits.

#### Scenario: Requests stream is trimmed
- **WHEN** messages are published to the request stream beyond the configured limit
- **THEN** the stream length is kept bounded by approximately the limit (oldest entries are dropped)

#### Scenario: Events stream has its own limit
- **WHEN** messages are published to the events stream
- **THEN** the events stream is bounded by its own (smaller) configured limit, independent of the request stream

#### Scenario: Dead-letter streams are bounded
- **WHEN** failed messages are moved to a dead-letter stream
- **THEN** the dead-letter stream is bounded by the configured limit

### Requirement: Purge of finished jobs
The system SHALL remove finished jobs (`done` or `failed`) whose last update is older than a configurable retention period, and SHALL keep active jobs and recent finished jobs.

#### Scenario: Old finished job removed
- **WHEN** the retention task runs and a `done` or `failed` job was last updated longer ago than the retention period
- **THEN** that job is deleted

#### Scenario: Active and recent jobs kept
- **WHEN** the retention task runs
- **THEN** jobs in `queued`/`running` state and finished jobs newer than the retention period are preserved

#### Scenario: Purge is idempotent
- **WHEN** the retention task runs again with no newly eligible jobs
- **THEN** it removes nothing and reports zero deletions

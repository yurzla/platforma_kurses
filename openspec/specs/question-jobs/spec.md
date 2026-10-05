# question-jobs

## Purpose

Decouples slow RAG generation from the HTTP request path: the API enqueues questions onto a Redis Streams bus, workers process them asynchronously, and clients poll durable job state in PostgreSQL.

## Requirements

### Requirement: Enqueue question as a job
The system SHALL accept a question for a chat session and enqueue it for asynchronous processing, returning immediately with a job identifier and HTTP 202.

#### Scenario: Question accepted
- **WHEN** a client submits a question for an existing session
- **THEN** the system creates a job in `queued` state and publishes the processing command to the Redis Streams bus
- **AND** the system responds with HTTP 202 and the job identifier

#### Scenario: Unknown session rejected
- **WHEN** a client submits a question for a non-existent session
- **THEN** the system responds with HTTP 404 and enqueues nothing

### Requirement: Durable job state
The system SHALL persist job state in PostgreSQL with the transitions `queued` -> `running` -> (`done` | `failed`), so that job status survives API and broker restarts.

#### Scenario: Worker completes a job
- **WHEN** a worker finishes processing a job successfully
- **THEN** in a single transaction it stores the assistant message and marks the job `done` with the answer, sources, and rewritten question

#### Scenario: Worker fails a job
- **WHEN** processing raises an unhandled error after retries are exhausted
- **THEN** the job is marked `failed` with an error description
- **AND** the failing message is moved to a dead-letter stream

#### Scenario: Status survives broker restart
- **WHEN** the broker is restarted while no worker is processing
- **THEN** previously completed job results remain readable by job identifier

### Requirement: Poll job status
The system SHALL expose job status by identifier, returning the current state and, when finished, the answer and sources.

#### Scenario: Running job polled
- **WHEN** a client polls a job that is `queued` or `running`
- **THEN** the system responds with HTTP 200 and the current status without an answer

#### Scenario: Finished job polled
- **WHEN** a client polls a job in `done` state
- **THEN** the system responds with HTTP 200, the status, the answer and the sources

#### Scenario: Unknown job
- **WHEN** a client polls a non-existent job identifier
- **THEN** the system responds with HTTP 404

### Requirement: Reliable delivery
The system SHALL consume the question stream with a consumer group and SHALL acknowledge a message only after its job reaches a terminal state, reclaiming pending messages from failed workers.

#### Scenario: Unacknowledged message reclaimed
- **WHEN** a worker crashes after reading a message without acknowledging it
- **THEN** another worker reclaims and processes the pending message

#### Scenario: Duplicate delivery is idempotent
- **WHEN** the same question message is delivered more than once
- **THEN** the job is not processed twice to a conflicting terminal state

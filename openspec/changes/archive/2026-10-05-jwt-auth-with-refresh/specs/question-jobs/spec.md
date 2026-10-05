## MODIFIED Requirements

### Requirement: Enqueue question as a job
The system SHALL accept a question for a chat session the caller owns and enqueue it for asynchronous processing, returning immediately with a job identifier and HTTP 202.

#### Scenario: Question accepted
- **WHEN** the session's owner submits a question for an existing session
- **THEN** the system creates a job in `queued` state and publishes the processing command to the Redis Streams bus
- **AND** the system responds with HTTP 202 and the job identifier

#### Scenario: Unknown session rejected
- **WHEN** a client submits a question for a non-existent session
- **THEN** the system responds with HTTP 404 and enqueues nothing

#### Scenario: Foreign session forbidden
- **WHEN** an authenticated user submits a question for a session owned by another user
- **THEN** the system responds with HTTP 403 and enqueues nothing

#### Scenario: Anonymous rejected
- **WHEN** an unauthenticated client submits a question
- **THEN** the system responds with HTTP 401 and enqueues nothing

### Requirement: Poll job status
The system SHALL expose job status by identifier, returning the current state and, when finished, the answer and sources, and SHALL only expose a job to the owner of its session or an administrator.

#### Scenario: Running job polled
- **WHEN** the session's owner polls a job that is `queued` or `running`
- **THEN** the system responds with HTTP 200 and the current status without an answer

#### Scenario: Finished job polled
- **WHEN** the session's owner polls a job in `done` state
- **THEN** the system responds with HTTP 200, the status, the answer and the sources

#### Scenario: Unknown job
- **WHEN** a client polls a non-existent job identifier
- **THEN** the system responds with HTTP 404

#### Scenario: Foreign job forbidden
- **WHEN** an authenticated user polls a job whose session is owned by another user
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous rejected
- **WHEN** an unauthenticated client polls a job
- **THEN** the system responds with HTTP 401

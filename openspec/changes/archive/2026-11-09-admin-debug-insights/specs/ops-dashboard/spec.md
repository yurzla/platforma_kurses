## ADDED Requirements

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

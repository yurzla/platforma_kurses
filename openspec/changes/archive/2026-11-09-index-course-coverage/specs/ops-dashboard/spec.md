## MODIFIED Requirements

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

# course-indexing Specification

## Purpose
Поддерживать семантический индекс описаний курсов, созданных преподавателями, без ручного запуска
batch-скрипта.

## Requirements

### Requirement: Asynchronous course description indexing

The system SHALL enqueue a course-indexing message after a teacher creates a course and after a
teacher changes its title or description. The request SHALL commit the course before enqueuing and
SHALL NOT wait for embedding generation.

#### Scenario: New course indexed

- **WHEN** a teacher successfully creates a course
- **THEN** the course is persisted and a course-indexing message is published
- **AND** the indexer creates an embedding for the current title and description when they contain text

#### Scenario: Relevant course update indexed

- **WHEN** a teacher successfully changes a course title or description
- **THEN** a course-indexing message is published after the update commits

#### Scenario: Unrelated course update not indexed

- **WHEN** a teacher changes only the level or publication state of a course
- **THEN** no course-indexing message is published

### Requirement: Asynchronous step material indexing

The system SHALL enqueue a step-indexing message after a teacher creates or saves a step. The
indexer SHALL use the latest persisted step content, classify text and video steps as `theory` and
other step types as `task`, and update only that step's chunks and embeddings.

#### Scenario: New step indexed

- **WHEN** a teacher successfully creates a text step
- **THEN** a `step_upsert` message is published after commit
- **AND** the indexer creates theory chunks and embeddings for that step

#### Scenario: Updated step re-indexed

- **WHEN** a teacher saves a changed step body
- **THEN** the indexer replaces the affected chunk text and embedding with the current content

#### Scenario: Deleted step removed from index

- **WHEN** a teacher deletes a step
- **THEN** its chunks and embeddings are deleted with the step

### Requirement: Current and idempotent course index

The indexer SHALL use the course's current persisted title and description, update both the indexed
chunk text and its embedding when text changes, and avoid generating a new embedding when the
current chunk is already indexed by the configured model.

#### Scenario: Repeated message for unchanged course

- **WHEN** the indexer receives a repeated message and the description chunk and active-model
  embedding already match the current course text
- **THEN** it completes without calling the embedding provider

#### Scenario: Message processed after a later edit

- **WHEN** a queued message is processed after the course was edited again
- **THEN** the indexer stores an embedding for the latest persisted course text

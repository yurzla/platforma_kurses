## MODIFIED Requirements

### Requirement: Indexing queue observability

The system SHALL report the state of the course and step indexing queue, including the number of
not-yet-processed messages, the number of delivered-but-unacknowledged messages, consumer lag, the
total number of messages retained in the stream, and the number of dead-letter entries produced by
indexing, so an administrator can detect stalled or failing indexing. The queue size SHALL count only
messages that are pending or not yet delivered and SHALL NOT count acknowledged messages that remain
in the stream until trimming.

#### Scenario: Index queue reported

- **WHEN** an administrator requests the index summary
- **THEN** the system returns the queue size, consumer-group pending and lag, and the total stream
  length

#### Scenario: Processed messages not counted as queued

- **WHEN** the indexing stream contains acknowledged messages that were already processed and no
  messages are pending or undelivered
- **THEN** the queue size is zero while the stream length still reflects the retained messages

#### Scenario: Indexing dead letters counted

- **WHEN** the indexing dead-letter stream contains entries
- **THEN** the index summary reports their count

#### Scenario: Indexing queue idle

- **WHEN** the indexing queue is empty and no consumers have pending messages
- **THEN** the index summary reports zero queue values without an error

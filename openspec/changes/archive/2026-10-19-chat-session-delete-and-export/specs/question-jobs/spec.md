## ADDED Requirements

### Requirement: Internal failure diagnostics

The system SHALL keep the technical failure description of a failed question job available to
operators through the job record, the dead-letter stream and the logs, and SHALL NOT present that
description to the end user as the assistant's answer. The user-facing assistant panel SHALL show a
neutral error message instead.

#### Scenario: Failure description persisted for operators
- **WHEN** processing a question raises an unhandled error and retries are exhausted
- **THEN** the job is marked `failed` with the technical description
- **AND** the description is available in the job record used by the administrator dashboard

#### Scenario: Technical description not shown to the user
- **WHEN** the assistant panel learns that a job has failed
- **THEN** the panel shows a neutral error message instead of the job's technical description

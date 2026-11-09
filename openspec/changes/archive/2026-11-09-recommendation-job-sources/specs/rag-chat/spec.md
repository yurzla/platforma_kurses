## ADDED Requirements

### Requirement: Recommendation job sources
The system SHALL persist the courses selected for a global recommendation answer as sources on both the job and the assistant message.

#### Scenario: Recommendation sources persisted
- **WHEN** a global session question is answered with recommended courses
- **THEN** the job and the assistant message store one source per recommended course

#### Scenario: Recommendation source metadata
- **WHEN** a recommendation source is stored
- **THEN** it contains the source type, course id, course title, course URL, and relevance score

#### Scenario: No recommendation matches
- **WHEN** no recommended courses are matched
- **THEN** the job stores no recommendation sources

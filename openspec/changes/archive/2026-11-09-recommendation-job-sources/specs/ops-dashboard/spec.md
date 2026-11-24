## ADDED Requirements

### Requirement: Recommendation sources in job details
The system SHALL display recommendation sources separately from chunk sources in job details.

#### Scenario: Recommended courses shown
- **WHEN** an administrator opens a job whose sources are course recommendations
- **THEN** the dashboard lists the recommended courses with links and relevance scores

#### Scenario: Chunk sources unchanged
- **WHEN** job details contain chunk sources
- **THEN** the dashboard continues to show chunk id, course, lesson, source type, and distance

#### Scenario: Empty sources message
- **WHEN** job details contain neither chunk nor recommendation sources
- **THEN** the dashboard reports that sources were not saved

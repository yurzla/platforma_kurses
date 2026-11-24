## ADDED Requirements

### Requirement: Job status cards scope
The dashboard SHALL show the job status summary cards only on the Jobs sub-tab.

#### Scenario: Cards visible on Jobs
- **WHEN** an administrator opens the Jobs sub-tab
- **THEN** the queued, running, done, and failed cards are visible

#### Scenario: Cards hidden on other sub-tabs
- **WHEN** an administrator opens the DLQ, Streams, index, chunks, or health sub-tab
- **THEN** the job status cards are not shown

#### Scenario: Card click filters jobs
- **WHEN** an administrator clicks a job status card
- **THEN** the dashboard opens the Jobs sub-tab with that status applied to the filter

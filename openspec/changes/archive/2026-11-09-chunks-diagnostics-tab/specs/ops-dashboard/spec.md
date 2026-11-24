## ADDED Requirements

### Requirement: Chunk inspection tab
The dashboard SHALL present chunk filtering and chunk listing in a dedicated diagnostics sub-tab separate from the index summary.

#### Scenario: Chunks tab opened
- **WHEN** an administrator opens the chunks sub-tab
- **THEN** the dashboard shows the chunk filters, chunk table, and pagination

#### Scenario: Index summary remains separate
- **WHEN** an administrator opens the index sub-tab
- **THEN** it shows the index totals, source-type breakdown, and per-course coverage without the chunk list

#### Scenario: Course filter available
- **WHEN** an administrator opens the chunks sub-tab without opening the index sub-tab first
- **THEN** the course filter is populated from the index summary

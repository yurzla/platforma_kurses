## ADDED Requirements

### Requirement: Filter toolbar layout
The dashboard SHALL render the Jobs and chunks filter panels as a single-row toolbar with equal-height controls and right-aligned actions, and SHALL truncate long course titles in the course filter.

#### Scenario: Jobs filters in one row
- **WHEN** an administrator opens the Jobs sub-tab
- **THEN** the status, session, and search fields stay on one row with the apply and reset buttons aligned to the right

#### Scenario: Chunks filters in one row
- **WHEN** an administrator opens the chunks sub-tab
- **THEN** the course, source type, and search fields stay on one row with the apply and reset buttons aligned to the right

#### Scenario: Equal control height
- **WHEN** a filter toolbar is rendered
- **THEN** inputs, selects, and buttons share the same height

#### Scenario: Long course title truncated
- **WHEN** a course title does not fit the course filter
- **THEN** the title is truncated with an ellipsis instead of widening the toolbar

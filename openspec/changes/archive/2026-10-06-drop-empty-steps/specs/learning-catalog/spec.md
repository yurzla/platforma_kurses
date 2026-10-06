## ADDED Requirements

### Requirement: Empty steps are not stored or exposed

The system SHALL store and expose only steps that have content: a step without any non-empty textual content SHALL be omitted from the course structure returned to clients, SHALL NOT be created during course import, and SHALL be removed by the cleanup procedure.

#### Scenario: Empty steps absent from the course structure

- **WHEN** an authenticated user requests a course whose lessons previously contained steps without textual content
- **THEN** the returned sections, lessons, and steps contain no contentless steps

#### Scenario: Import skips empty steps

- **WHEN** a course is imported and a source step has no textual content
- **THEN** that step is not persisted and the reported step count excludes it

#### Scenario: Cleanup removes empty steps

- **WHEN** the cleanup procedure runs and the database contains steps without textual content
- **THEN** those steps are deleted together with their step content and user progress records

### Requirement: Step positions are sequential within a lesson

The system SHALL number the steps of each lesson consecutively starting from 1, preserving their relative order, after empty steps are removed and after a course is imported.

#### Scenario: Numbering starts at one without gaps

- **WHEN** the course structure is returned for a lesson
- **THEN** the lesson's steps are numbered 1 through N with no gaps

#### Scenario: Removal renumbers the remaining steps

- **WHEN** an empty step is removed from a lesson
- **THEN** the remaining steps of that lesson are renumbered consecutively from 1

#### Scenario: Import numbers steps per lesson

- **WHEN** a course is imported
- **THEN** the steps of each lesson are numbered consecutively from 1

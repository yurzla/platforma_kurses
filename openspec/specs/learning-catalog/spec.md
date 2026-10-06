# learning-catalog Specification

## Purpose
Учебный каталог для студентов: список курсов с прогрессом, структура курса (секции/уроки/шаги), просмотр шага и отправка ответа с серверной оценкой и обновлением прогресса.

## Requirements

### Requirement: Course catalog
The system SHALL expose the list of published courses with lesson/step counts and, for the authenticated user, enrollment and progress information.

#### Scenario: Courses listed
- **WHEN** an authenticated user requests the course list
- **THEN** the system returns the published courses with counts and the user's progress

#### Scenario: Authentication required
- **WHEN** an unauthenticated client requests the course catalog
- **THEN** the system responds with HTTP 401

### Requirement: Course structure
The system SHALL expose a course's sections, lessons, and steps in order, marking the steps the user has completed.

#### Scenario: Course detail
- **WHEN** an authenticated user requests a course
- **THEN** the system returns its sections, lessons, and steps ordered by position

#### Scenario: Completed steps marked
- **WHEN** the user has passed or completed a step
- **THEN** that step is reported as completed

### Requirement: Step view without answer keys
The system SHALL expose a step's content and answer options but SHALL NOT reveal which options are correct before the user submits an answer.

#### Scenario: Step detail
- **WHEN** an authenticated user requests a step
- **THEN** the system returns the step type, content, and (for choice tasks) the answer options without correctness flags

#### Scenario: Manual step
- **WHEN** a step's type has no automatic grading
- **THEN** the step is reported as manually graded

### Requirement: Answer submission and progress
The system SHALL evaluate a submitted answer server-side, record the attempt, and recompute the course progress.

#### Scenario: Correct auto-graded answer
- **WHEN** a user submits the correct answer to an auto-graded step
- **THEN** the system reports the answer as correct and marks the step passed

#### Scenario: Incorrect answer
- **WHEN** a user submits an incorrect answer
- **THEN** the system reports the answer as incorrect and records a failed attempt

#### Scenario: Manual completion
- **WHEN** a user submits an answer to a manually graded step
- **THEN** the system records the step as completed without a correctness verdict

#### Scenario: Progress recomputed
- **WHEN** a step result is recorded
- **THEN** the system recomputes and stores the course progress percentage

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

### Requirement: Filter courses by enrollment

The course catalog SHALL support returning only the courses in which the authenticated user has enrollment when the list endpoint is called with the `enrolled=true` filter, while returning all published courses when the filter is absent.

#### Scenario: Enrolled filter applied

- **WHEN** an authenticated user requests the course list with `enrolled=true`
- **THEN** the system returns only the published courses that have an enrollment of that user

#### Scenario: No filter returns full catalog

- **WHEN** an authenticated user requests the course list without the enrolled filter
- **THEN** the system returns all published courses with the user's enrollment and progress information

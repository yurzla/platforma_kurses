## MODIFIED Requirements

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

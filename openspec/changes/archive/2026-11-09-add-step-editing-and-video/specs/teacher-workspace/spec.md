# teacher-workspace delta

## ADDED Requirements

### Requirement: Teacher step management

The teacher workspace SHALL allow the owner of a course to edit and delete steps inside its lessons. Editing SHALL support changing the step type, the material or task body, choice options, the correct answer for auto-graded input steps, and an optional video URL. Deleting a step SHALL remove its dependent content and SHALL renumber the remaining steps of the lesson sequentially from one. Non-owners SHALL be denied.

#### Scenario: Step edit data available

- **WHEN** a teacher opens their course details
- **THEN** every step exposes its type, body, choice options, correct answer, and video URL when present

#### Scenario: Update step type and body

- **WHEN** the teacher updates a step with a new type and body
- **THEN** the step type and body are changed and data that no longer applies to the new type is removed

#### Scenario: Video URL on any step

- **WHEN** the teacher saves a valid video URL on a step of any type
- **THEN** the URL is stored and returned with the step

#### Scenario: Delete step and renumber

- **WHEN** the teacher deletes a step from a lesson
- **THEN** the step and its dependent rows are removed and the remaining steps are numbered from one without gaps

#### Scenario: Foreign step denied

- **WHEN** a teacher tries to edit or delete a step of another teacher's course
- **THEN** the system responds with HTTP 404

#### Scenario: Invalid step data rejected

- **WHEN** the payload has no options for a choice step, no correct answer for an auto-graded input step, or an unsafe video URL
- **THEN** the system responds with HTTP 422 and the step is unchanged

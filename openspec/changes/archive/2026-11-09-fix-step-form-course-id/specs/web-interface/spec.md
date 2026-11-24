# web-interface delta

## ADDED Requirements

### Requirement: Step form returns to the course page

After creating, saving, or deleting a step, the web service SHALL redirect the teacher back to the edited course page. The step form SHALL submit the identifier of the course it belongs to.

#### Scenario: Saving a step

- **WHEN** a teacher submits the step form
- **THEN** the response redirects to `/teacher/courses/{course_id}` for the course being edited

#### Scenario: Deleting a step

- **WHEN** a teacher confirms deletion of a step
- **THEN** the response redirects to the same course page

#### Scenario: Course id submitted with the form

- **WHEN** the step form is rendered
- **THEN** its hidden `course_id` field contains the current course identifier rather than an empty value

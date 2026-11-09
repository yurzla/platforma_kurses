# web-interface delta

## MODIFIED Requirements

### Requirement: Step editing UI

The teacher course page SHALL render each lesson step as a card with an inline editable form and a delete control. The step form SHALL place the step type, the material or task body, the optional video URL, the type-specific fields, and the submit control on separate full-width rows. The form SHALL include a formatting hint describing supported Markdown syntax and the video URL field. The student step page SHALL render the step video as a player.

#### Scenario: Inline edit form

- **WHEN** a teacher opens their course page
- **THEN** every step has a collapsible edit form prefilled with its current data and a delete control

#### Scenario: Stacked fields

- **WHEN** the step form is rendered
- **THEN** the type, body, video URL, type-specific fields, and submit button each occupy their own row

#### Scenario: Type-specific fields toggle

- **WHEN** the teacher changes the step type
- **THEN** only the choice fields, the correct-answer field, or neither are shown as appropriate, while the video URL field stays available

#### Scenario: Choice option row

- **WHEN** the choice fields are rendered
- **THEN** each correct-answer checkbox and its option text input appear on the same row, and the multiple-choice checkbox appears on the same row as its label

#### Scenario: Formatting hint

- **WHEN** the teacher edits or creates a step
- **THEN** a hint describes Markdown syntax and explains that video is added through the video URL field

#### Scenario: Markdown hint examples

- **WHEN** the teacher opens the formatting hint
- **THEN** it shows examples for emphasis, headings, lists, links, code, and line breaks

#### Scenario: Delete step

- **WHEN** the teacher confirms deletion of a step
- **THEN** the step disappears from the lesson and the remaining steps are renumbered

#### Scenario: Video player on step page

- **WHEN** a step has a recognized video URL
- **THEN** the student step page shows an embedded player above the step body

### Requirement: Step form returns to the course page

After creating, saving, or deleting a step, the web service SHALL redirect the teacher back to the edited course page. The step form SHALL submit the identifier of the course it belongs to.

#### Scenario: Saving a step

- **WHEN** a teacher submits the step form
- **THEN** the response redirects to `/teacher/courses/{course_id}` for the course being edited

#### Scenario: Creating a step

- **WHEN** a teacher submits the create-step form
- **THEN** the request is handled by the step creation route and is not rejected as an invalid dictionary body

#### Scenario: Deleting a step

- **WHEN** a teacher confirms deletion of a step
- **THEN** the response redirects to the same course page

#### Scenario: Course id submitted with the form

- **WHEN** the step form is rendered
- **THEN** its hidden `course_id` field contains the current course identifier rather than an empty value

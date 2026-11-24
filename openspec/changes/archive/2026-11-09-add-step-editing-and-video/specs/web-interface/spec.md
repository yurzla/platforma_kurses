# web-interface delta

## ADDED Requirements

### Requirement: Step editing UI

The teacher course page SHALL render each lesson step as a card with an inline editable form and a delete control. The step form SHALL place the step type, the material or task body, the optional video URL, the type-specific fields, and the submit control on separate full-width rows. The form SHALL include a formatting hint describing supported HTML and the video URL field. The student step page SHALL render the step video as a player.

#### Scenario: Inline edit form

- **WHEN** a teacher opens their course page
- **THEN** every step has a collapsible edit form prefilled with its current data and a delete control

#### Scenario: Stacked fields

- **WHEN** the step form is rendered
- **THEN** the type, body, video URL, type-specific fields, and submit button each occupy their own row

#### Scenario: Type-specific fields toggle

- **WHEN** the teacher changes the step type
- **THEN** only the choice fields, the correct-answer field, or neither are shown as appropriate, while the video URL field stays available

#### Scenario: Formatting hint

- **WHEN** the teacher edits or creates a step
- **THEN** a hint lists supported HTML tags and explains that video is added through the video URL field

#### Scenario: Delete step

- **WHEN** the teacher confirms deletion of a step
- **THEN** the step disappears from the lesson and the remaining steps are renumbered

#### Scenario: Video player on step page

- **WHEN** a step has a recognized video URL
- **THEN** the student step page shows an embedded player above the step body

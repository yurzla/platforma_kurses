## ADDED Requirements

### Requirement: Step type badge and answer form

The step page SHALL show the step type as a human-readable label in a badge and SHALL choose the
answer form by the step type, rendering choice options for choice steps instead of a text input.

#### Scenario: Badge shows the step type
- **WHEN** the user opens a text step
- **THEN** the badge shows «Текст»
- **AND** the badge is not empty

#### Scenario: Choice step shows options
- **WHEN** the user opens a choice step with available options
- **THEN** the page shows the answer options as radio buttons or checkboxes
- **AND** the badge shows «Тест»

#### Scenario: Unknown step type falls back to its raw name
- **WHEN** a step has a type without a translated label
- **THEN** the badge shows the raw type string

## MODIFIED Requirements

### Requirement: Course progress bar on the step page

The step page SHALL show a course progress bar without a surrounding card, with the completed share
and the number of completed steps out of the total, marking module boundaries with larger dots and
lesson boundaries with smaller dots. Dots reached by the completed progress SHALL have an accent
outline. When the user marks the step completed, the bar SHALL update without a page reload.

#### Scenario: Progress reflects the whole course
- **WHEN** the user opens a step of a course
- **THEN** the page shows the course percent and «Пройдено N из M шагов»
- **AND** the bar fill width and `aria-valuenow` equal the course percent

#### Scenario: Module checkpoints on the bar
- **WHEN** the course has several modules with steps
- **THEN** the bar shows a larger dot at each cumulative module boundary except the end
- **AND** each module dot has a tooltip with the module title

#### Scenario: Lesson markers on the bar
- **WHEN** a module contains several lessons
- **THEN** the end of each lesson except the module end is shown as a smaller dot
- **AND** a lesson ending exactly at the module boundary does not add a second dot

#### Scenario: Reached markers are outlined
- **WHEN** the completed progress is at or beyond a checkpoint
- **THEN** that dot is outlined in the accent colour
- **AND** dots beyond the current progress keep the plain style

#### Scenario: Completed step is counted
- **WHEN** the opened step is already completed
- **THEN** it is included in the completed steps of the progress bar

#### Scenario: Progress updates after completion
- **WHEN** the user marks a manual step completed and the server confirms
- **THEN** the completed counter, percent and bar fill grow by one step immediately
- **AND** the accent outline of newly reached dots appears immediately
- **AND** no page reload is required

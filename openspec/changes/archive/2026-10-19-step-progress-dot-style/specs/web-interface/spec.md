## MODIFIED Requirements

### Requirement: Course progress bar on the step page

The step page SHALL show a course progress bar without a surrounding card, with the completed share
and the number of completed steps out of the total, marking module boundaries with larger dots and
lesson boundaries with smaller dots. Dots SHALL have a white fill and a grey outline that switches
to the accent colour when the completed progress reaches them. When the user marks the step
completed, the bar SHALL update without a page reload.

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

#### Scenario: Plain dots are white with a grey outline
- **WHEN** a checkpoint is beyond the completed progress
- **THEN** the dot has a white fill and a grey outline

#### Scenario: Reached markers are outlined
- **WHEN** the completed progress is at or beyond a checkpoint
- **THEN** the dot keeps its white fill and gets an accent outline instead of the grey one
- **AND** dots beyond the current progress keep the grey outline

#### Scenario: Completed step is counted
- **WHEN** the opened step is already completed
- **THEN** it is included in the completed steps of the progress bar

#### Scenario: Progress updates after completion
- **WHEN** the user marks a manual step completed and the server confirms
- **THEN** the completed counter, percent and bar fill grow by one step immediately
- **AND** the accent outline of newly reached dots appears immediately
- **AND** no page reload is required

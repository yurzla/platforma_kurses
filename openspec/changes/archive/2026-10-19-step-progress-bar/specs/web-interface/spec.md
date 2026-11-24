## ADDED Requirements

### Requirement: Course progress bar on the step page

The step page SHALL show a progress bar of the whole course with the completed share, the number
of completed steps out of the total, and a checkpoint mark at every module boundary except the end
of the bar. When the user marks the step completed, the bar SHALL update without a page reload.

#### Scenario: Progress reflects the whole course
- **WHEN** the user opens a step of a course
- **THEN** the page shows the course percent and «Пройдено N из M шагов»
- **AND** the bar fill width and `aria-valuenow` equal the course percent

#### Scenario: Module checkpoints on the bar
- **WHEN** the course has several modules with steps
- **THEN** the bar shows a checkpoint at each cumulative module boundary except the end
- **AND** each checkpoint has a tooltip with the module title and its completed and total steps

#### Scenario: Completed step is counted
- **WHEN** the opened step is already completed
- **THEN** it is included in the completed steps of the progress bar

#### Scenario: Progress updates after completion
- **WHEN** the user marks a manual step completed and the server confirms
- **THEN** the completed counter, percent and bar fill grow by one step immediately
- **AND** no page reload is required

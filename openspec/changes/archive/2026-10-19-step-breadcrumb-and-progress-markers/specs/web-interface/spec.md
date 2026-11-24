## ADDED Requirements

### Requirement: Step page breadcrumbs

The step page SHALL show the breadcrumb trail `Курсы / <course> / <module> / <lesson> / Шаг N`,
where the course name links to the course page, `N` is the step number in the whole course, and the
word «Шаг» starts with a capital letter.

#### Scenario: Breadcrumbs show the course hierarchy
- **WHEN** the user opens a step that belongs to a module and a lesson
- **THEN** the breadcrumbs contain the course title, the module title and the lesson title
- **AND** the course title is a link to the course page

#### Scenario: Breadcrumbs show the step number
- **WHEN** the user opens the second step of the course
- **THEN** the trail ends with «Шаг 2»

## MODIFIED Requirements

### Requirement: Course progress bar on the step page

The step page SHALL show a course progress bar without a surrounding card, with the completed share
and the number of completed steps out of the total, marking module boundaries with larger dots and
lesson boundaries with smaller dots. When the user marks the step completed, the bar SHALL update
without a page reload.

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

#### Scenario: Completed step is counted
- **WHEN** the opened step is already completed
- **THEN** it is included in the completed steps of the progress bar

#### Scenario: Progress updates after completion
- **WHEN** the user marks a manual step completed and the server confirms
- **THEN** the completed counter, percent and bar fill grow by one step immediately
- **AND** no page reload is required

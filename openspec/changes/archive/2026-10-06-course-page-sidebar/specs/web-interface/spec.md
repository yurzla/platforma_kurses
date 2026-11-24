## ADDED Requirements

### Requirement: Course page with progress sidebar and section tabs

The web service SHALL render the course page with a persistent left sidebar that shows the user's progress through the course and offers a choice between the «Описание» (description) and «Содержание» (content) sections, rendering the selected section next to the sidebar. The progress block SHALL show the completion percentage, the number of completed and total steps, and a control to continue at the first not-yet-completed step (or an indication that the course is complete).

#### Scenario: Progress shown on the course page

- **WHEN** an authenticated user requests a course page
- **THEN** the page contains a sidebar block with the completion percentage, the «пройдено X из Y шагов» counter, and a progress bar

#### Scenario: Progress reflects completed steps

- **WHEN** some of the course steps have been passed by the user
- **THEN** the sidebar reports the percentage computed from the passed steps relative to the total steps

#### Scenario: Continue control targets the next step

- **WHEN** the course has at least one step not yet passed
- **THEN** the sidebar offers a control linking to the page of the first not-yet-completed step

#### Scenario: Completed course indication

- **WHEN** every step of the course has been passed
- **THEN** the sidebar indicates that the course is complete instead of offering a continue control

#### Scenario: Switching between description and content

- **WHEN** the user selects the «Содержание» section in the sidebar
- **THEN** the content section with the course structure is displayed next to the sidebar
- **AND WHEN** the user selects the «Описание» section
- **THEN** the description section is displayed next to the sidebar

### Requirement: Formatted course description

The web service SHALL render the course description as formatted text that preserves paragraph and line breaks, and the course import SHALL preserve the source description's paragraph and line breaks instead of collapsing the text into a single line.

#### Scenario: Description line breaks preserved

- **WHEN** a stored course description contains line breaks
- **THEN** the course page renders the description preserving those breaks as separate paragraphs or lines

#### Scenario: Import preserves description structure

- **WHEN** a course with an HTML description containing paragraph or line-break markup is imported
- **THEN** the stored description keeps the paragraph and line boundaries as newlines and contains no markup tags

### Requirement: Module and lesson accordions on the course page

The web service SHALL present the course structure in the content section as collapsible modules and lessons, where each module and lesson header shows its title and step count, and each step is a link to the step page marked as completed when the user has passed it.

#### Scenario: Modules and lessons are collapsible

- **WHEN** the course page content section is rendered
- **THEN** each module and each lesson can be expanded or collapsed and its header shows the title and number of steps

#### Scenario: Steps link to the step page

- **WHEN** a step is displayed in the content section
- **THEN** it links to the step page of that course step

#### Scenario: Completed steps marked in the structure

- **WHEN** the user has passed a step
- **THEN** that step is marked as completed in the content section

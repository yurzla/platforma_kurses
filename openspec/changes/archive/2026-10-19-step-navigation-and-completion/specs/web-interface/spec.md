## ADDED Requirements

### Requirement: Step page navigation and completion state

The step page SHALL link to the previous and next steps of the course in course order, and SHALL
show a disabled control where no previous or next step exists. For a manually graded step the page
SHALL show «Отметить выполненным» until the step is completed and a disabled green «Выполнено»
afterwards, including immediately after the user marks it completed.

#### Scenario: Previous and next links
- **WHEN** the user opens a step that has both neighbours in the course structure
- **THEN** the page shows links to the previous and the next step
- **AND** the links point to the corresponding step pages of the same course

#### Scenario: Edges of the course
- **WHEN** the user opens the first or the last step of the course
- **THEN** the missing direction is shown as a disabled control
- **AND** no link to a non-existent step is rendered

#### Scenario: Neighbours follow course order across lessons
- **WHEN** a step is the last one of its lesson but the next lesson has a step
- **THEN** «Вперёд» leads to the first step of the next lesson

#### Scenario: Completed manual step on load
- **WHEN** the user opens a manually graded step that is already completed
- **THEN** the page shows a green disabled «Выполнено» control instead of «Отметить выполненным»

#### Scenario: Marking a step completed
- **WHEN** the user marks a manual step completed and the server confirms
- **THEN** the control immediately becomes a green disabled «Выполнено»
- **AND** it cannot send a second completion request

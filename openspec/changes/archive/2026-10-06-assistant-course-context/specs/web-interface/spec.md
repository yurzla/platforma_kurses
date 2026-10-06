## ADDED Requirements

### Requirement: Assistant course context label

On the course page and the step page the assistant panel SHALL display the title of the current
course so that the user understands questions are answered only within that course. On the courses
list and the «Мое обучение» list, where the assistant is not bound to a course, no course label
SHALL be shown.

#### Scenario: Course title shown on the course page
- **WHEN** an authenticated user opens the assistant on the course page
- **THEN** the panel shows a label with the current course title

#### Scenario: Course title shown on the step page
- **WHEN** an authenticated user opens the assistant on a step page
- **THEN** the panel shows a label with the title of the step's course

#### Scenario: No course label on list pages
- **WHEN** an authenticated user opens the assistant on the courses list or the «Мое обучение» list
- **THEN** the panel shows no course label

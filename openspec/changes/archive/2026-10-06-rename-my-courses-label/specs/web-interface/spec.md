## MODIFIED Requirements

### Requirement: My courses page

The web service SHALL serve a «Мое обучение» page that lists only the courses the authenticated user has already started, showing each course's progress and lesson/step counts, and SHALL provide a navigation entry to this page for authenticated users. When the user has not started any course, the page SHALL show an empty-state message linking to the course catalog.

#### Scenario: Only started courses listed

- **WHEN** an authenticated user requests the «Мое обучение» page
- **THEN** the page lists exactly the courses in which the user has enrollment, together with their progress

#### Scenario: Navigation entry available

- **WHEN** an authenticated user views a learning page
- **THEN** the navigation contains a link to the «Мое обучение» page

#### Scenario: Empty state

- **WHEN** an authenticated user without enrollments requests the «Мое обучение» page
- **THEN** the page shows a message that no course has been started yet and a link to the course catalog

#### Scenario: Authentication required

- **WHEN** an unauthenticated client requests the «Мое обучение» page
- **THEN** the web service redirects to the login page

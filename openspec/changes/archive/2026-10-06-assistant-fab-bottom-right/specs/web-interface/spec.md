## MODIFIED Requirements

### Requirement: Floating RAG assistant widget

The web service SHALL render a pinned assistant control at the bottom-right of the course page and the step page and SHALL open a RAG chat panel overlaid on the right side of the page when the control is activated, without shifting the page content. The control and the panel SHALL NOT be rendered on the courses list, the administrator page, the login page, or the registration page.

#### Scenario: Assistant control visible on course and step pages

- **WHEN** an authenticated user requests the course page or a step page
- **THEN** the web service returns the page containing a fixed assistant control pinned at the bottom-right

#### Scenario: Assistant absent on the courses list

- **WHEN** a client requests the courses list page
- **THEN** the response contains no assistant control and no chat panel

#### Scenario: Assistant absent on the administrator page

- **WHEN** an authenticated administrator requests the administrator page
- **THEN** the response contains no assistant control and no chat panel

#### Scenario: Assistant absent on unauthenticated pages

- **WHEN** a client requests the login or registration page
- **THEN** the response contains no assistant control and no chat panel

#### Scenario: Opening the chat panel

- **WHEN** the user activates the assistant control
- **THEN** the chat panel becomes visible overlaid on the right side of the page while the page content stays in place

#### Scenario: Course context reused

- **WHEN** the user asks a question from the chat panel
- **THEN** a chat session is created for the current page's course without requiring the user to choose a course

#### Scenario: Question answered through job polling

- **WHEN** the user submits a question in the chat panel
- **THEN** the panel enqueues the question, polls the job status, and renders the assistant answer when the job completes

#### Scenario: Session required for asking

- **WHEN** the API responds with HTTP 401 while creating a session or asking a question
- **THEN** the browser is redirected to the login page

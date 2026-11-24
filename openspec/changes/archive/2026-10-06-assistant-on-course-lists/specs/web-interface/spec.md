## REMOVED Requirements

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

## ADDED Requirements

### Requirement: Floating RAG assistant widget on learning and list pages

The web service SHALL render a pinned assistant control at the bottom-right of the course page, the step page, the courses list and the «Мое обучение» list, and SHALL open a RAG chat panel overlaid on the right side of the page when the control is activated, without shifting the page content. The control and the panel SHALL NOT be rendered on the administrator page, the login page, or the registration page.

#### Scenario: Assistant control visible on course and step pages

- **WHEN** an authenticated user requests the course page or a step page
- **THEN** the web service returns the page containing a fixed assistant control pinned at the bottom-right

#### Scenario: Assistant visible on the courses list

- **WHEN** an authenticated user requests the courses list page
- **THEN** the web service returns the page containing the assistant control and the chat panel

#### Scenario: Assistant visible on the my-courses list

- **WHEN** an authenticated user requests the «Мое обучение» page
- **THEN** the web service returns the page containing the assistant control and the chat panel

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

- **WHEN** the user asks a question from the chat panel on the course page or a step page
- **THEN** a chat session is created for the current page's course without requiring the user to choose a course

#### Scenario: Question answered through job polling

- **WHEN** the user submits a question in the chat panel
- **THEN** the panel enqueues the question, polls the job status, and renders the assistant answer when the job completes

#### Scenario: Session required for asking

- **WHEN** the API responds with HTTP 401 while creating a session or asking a question
- **THEN** the browser is redirected to the login page

#### Scenario: Global question on list pages

- **WHEN** the user submits a question on the courses list or the «Мое обучение» list without an open session
- **THEN** the panel creates a session not bound to a single course so that the answer considers all courses

### Requirement: Course-grouped chat history

The assistant chat panel SHALL show the user's past chat sessions grouped by course, each group collapsible and showing a preview of the last message of each session, and SHALL let the user open a session to load its history and continue the conversation. On the courses list and the «Мое обучение» list the panel SHALL show sessions of all courses; on the course page and the step page it SHALL show only the sessions of the current course. The panel SHALL reload the session list from the server when the drawer is opened and when the user returns to the history, so that newly created sessions and updated previews appear without a full page reload.

#### Scenario: History grouped by course

- **WHEN** an authenticated user opens the assistant
- **THEN** the panel lists the user's chat sessions grouped under their course titles, each group collapsed by default with a session count

#### Scenario: Expanding a course group

- **WHEN** the user expands a course group
- **THEN** the sessions of that course become visible, each with its start time and a preview of the last message

#### Scenario: Open and continue a session

- **WHEN** the user selects a session in the history
- **THEN** the panel loads that session's messages and further questions are sent to the same session

#### Scenario: History refreshed when the drawer opens

- **WHEN** the user opens the assistant drawer
- **THEN** the panel reloads the session list from the server before showing it

#### Scenario: History refreshed on returning

- **WHEN** the user returns to the history from a conversation using the «К истории» button
- **THEN** the panel reloads the session list so that a session created during the conversation appears with its preview

#### Scenario: History on the course page

- **WHEN** an authenticated user opens the assistant on the course page or a step page
- **THEN** the panel shows only the sessions belonging to the current course

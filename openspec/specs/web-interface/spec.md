# web-interface Specification

## Purpose
Отдельный сервис визуализации: отдаёт HTML-страницы (вход, обучение, дашборд), проксирует запросы браузера к JSON API и пробрасывает cookie сессии, не храня состояние аутентификации сам.

## Requirements

### Requirement: HTML pages served by the web service
The web service SHALL serve the user-facing HTML pages: a login page, a registration page, the learning pages, and the administrator page named «Админ панель».

#### Scenario: Login page
- **WHEN** a client requests the login page
- **THEN** the web service returns an HTML page with a single email and password form and a link to registration

#### Scenario: Registration page
- **WHEN** a client requests the registration page
- **THEN** the web service returns an HTML page with fields for email, name, password, and a role choice limited to student or teacher

#### Scenario: Administrator page
- **WHEN** an authenticated administrator requests the administrator page
- **THEN** the web service returns an HTML page titled «Админ панель» with tabs for operational data and a users section

#### Scenario: Health endpoint
- **WHEN** a client requests the web health endpoint
- **THEN** the web service responds with HTTP 200

### Requirement: Transparent API proxy
The web service SHALL proxy requests under `/api/*` to the API, forwarding the request method, query string, body, and relevant headers (including the auth cookie or `Authorization` header), and SHALL relay response cookies back to the browser. When the API responds with HTTP 401 and the browser holds a refresh cookie, the web service SHALL transparently refresh the access token and retry the request.

#### Scenario: Request forwarded
- **WHEN** a client requests `/api/v1/...` from the web service
- **THEN** the web service forwards the request to the API and returns the upstream status, body, and headers

#### Scenario: Session cookie relayed
- **WHEN** the API sets or clears an auth cookie in response to a proxied request
- **THEN** the web service relays the `Set-Cookie` header to the browser

#### Scenario: Authorization forwarded
- **WHEN** a client sends an `Authorization` header to the web service
- **THEN** the web service forwards that header to the API

#### Scenario: Access token auto-refreshed
- **WHEN** the API responds with HTTP 401 to a proxied request and the request carries a valid refresh cookie
- **THEN** the web service refreshes the token pair, retries the original request with the new access token, and relays the new cookies to the browser

### Requirement: Login and registration dispatch
The web service SHALL submit the login form to the single login API endpoint, SHALL submit the registration form to the registration API endpoint, and SHALL redirect authenticated users to the page appropriate to their role.

#### Scenario: Successful login
- **WHEN** a client submits valid credentials
- **THEN** the web service redirects an administrator to the administrator page and any other role to the courses page

#### Scenario: Registration and auto-login
- **WHEN** a client submits a valid registration with role student or teacher
- **THEN** the web service establishes a session and redirects to the courses page

#### Scenario: Failed login
- **WHEN** a client submits invalid credentials
- **THEN** the web service re-renders the login page with an error and does not establish a session

#### Scenario: Failed registration
- **WHEN** a client registers with a duplicate email or the admin role
- **THEN** the web service re-renders the registration page with an error and does not create a user

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

The web service SHALL render the course description as formatted text that preserves paragraph and line breaks, and the course import SHALL preserve the source description's paragraph and line breaks instead of collapsing the text into a single line. The course import SHALL decode HTML entities (such as `&nbsp;`, `&gt;`, `&amp;`) and normalize non-breaking spaces to plain spaces, so the stored description contains no markup tags, HTML entities, or non-breaking spaces.

#### Scenario: Description line breaks preserved

- **WHEN** a stored course description contains line breaks
- **THEN** the course page renders the description preserving those breaks as separate paragraphs or lines

#### Scenario: Import preserves description structure

- **WHEN** a course with an HTML description containing paragraph or line-break markup is imported
- **THEN** the stored description keeps the paragraph and line boundaries as newlines and contains no markup tags

#### Scenario: Import decodes HTML entities

- **WHEN** a course description contains HTML entities such as `&nbsp;` or `&gt;`
- **THEN** the stored description contains the decoded characters with plain spaces instead of non-breaking spaces, and no entities remain

#### Scenario: Existing descriptions are normalized

- **WHEN** the description-normalization script runs over stored courses
- **THEN** descriptions containing entities or non-breaking spaces are rewritten to the decoded text and clean descriptions are left unchanged

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

### Requirement: Course list pagination and layout

The web service SHALL show the course lists (`/courses` and `/my-courses`) as pages of at most 10 courses, SHALL render page navigation (previous/next controls and page numbers) when more than one page exists, and SHALL lay the course cards out in two columns on wide screens and a single column on narrow screens.

#### Scenario: At most ten courses per page

- **WHEN** an authenticated user opens a course list page
- **THEN** the page shows at most 10 course cards

#### Scenario: Page navigation shown for multiple pages

- **WHEN** the course list has more courses than fit on one page
- **THEN** the page shows previous/next controls and page numbers linking to the other pages

#### Scenario: Requesting a specific page

- **WHEN** the user opens a course list page with the `page` parameter
- **THEN** the page shows the corresponding slice of courses and highlights the current page number

#### Scenario: No navigation for a single page

- **WHEN** the course list fits on a single page
- **THEN** the page shows no page navigation controls

#### Scenario: Two-column card grid

- **WHEN** a course list page is rendered on a wide screen
- **THEN** the course cards are arranged in two columns, collapsing to a single column on narrow screens

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

### Requirement: Formatted assistant answers

The assistant chat panel SHALL render assistant answers as Markdown: text wrapped in double
asterisks SHALL be shown in bold, a triple-backtick fenced code block SHALL be shown as a framed
code block preserving line breaks, and inline code in single backticks SHALL be shown as framed
inline code. Text without Markdown SHALL be shown unchanged, preserving line breaks. Answers SHALL
be inserted as DOM nodes without interpreting raw HTML from the model.

#### Scenario: Bold text rendered
- **WHEN** an assistant answer contains `**важное**`
- **THEN** the panel shows «важное» in bold without the surrounding asterisks

#### Scenario: Fenced code block framed
- **WHEN** an assistant answer contains a fenced code block
- **THEN** the panel shows the code in a framed block with its line breaks preserved and without the fence markers

#### Scenario: Inline code framed
- **WHEN** an assistant answer contains inline code in backticks
- **THEN** the panel shows it as framed inline code without the backticks

#### Scenario: Plain answer preserved
- **WHEN** an assistant answer contains no Markdown
- **THEN** the panel shows the text unchanged, preserving line breaks

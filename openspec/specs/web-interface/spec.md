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
code block preserving line breaks, inline code in single backticks SHALL be shown as framed inline
code, and a Markdown link `[text](target)` SHALL be shown as a clickable link. Only relative
targets that start with `/` and contain no scheme and no `//` SHALL be rendered as links; any other
target SHALL be shown as plain text. Text without Markdown SHALL be shown unchanged, preserving
line breaks. Answers SHALL be inserted as DOM nodes without interpreting raw HTML from the model.

#### Scenario: Bold text rendered
- **WHEN** an assistant answer contains `**важное**`
- **THEN** the panel shows «важное» in bold without the surrounding asterisks

#### Scenario: Fenced code block framed
- **WHEN** an assistant answer contains a fenced code block
- **THEN** the panel shows the code in a framed block with its line breaks preserved and without the fence markers

#### Scenario: Inline code framed
- **WHEN** an assistant answer contains inline code in backticks
- **THEN** the panel shows it as framed inline code without the backticks

#### Scenario: Course link rendered
- **WHEN** an assistant answer contains `[«Курс»](/courses/5)`
- **THEN** the panel shows «Курс» as a clickable link to `/courses/5` without the Markdown syntax

#### Scenario: Non-portal link shown as text
- **WHEN** an assistant answer contains a Markdown link whose target is not a relative platform path (for example `https://example.com`)
- **THEN** the panel shows the link text and target as plain text and does not create a link

#### Scenario: Plain answer preserved
- **WHEN** an assistant answer contains no Markdown
- **THEN** the panel shows the text unchanged, preserving line breaks

### Requirement: Assistant drawer placement and dismissal

The assistant chat panel SHALL be rendered as a floating, rounded window positioned below the top
navigation bar so that it does not cover the navigation bar, and SHALL close when the user clicks
outside the panel. Clicking inside the panel SHALL NOT close it.

#### Scenario: Panel below the navigation bar
- **WHEN** the user opens the assistant panel
- **THEN** the panel is shown below the top navigation bar without covering it

#### Scenario: Rounded panel
- **WHEN** the assistant panel is visible
- **THEN** it is drawn as a rounded floating window

#### Scenario: Outside click closes the panel
- **WHEN** the assistant panel is open and the user clicks outside the panel
- **THEN** the panel closes

#### Scenario: Inside click keeps the panel open
- **WHEN** the assistant panel is open and the user clicks inside the panel
- **THEN** the panel stays open

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

### Requirement: Delete chat session from history

The assistant chat panel SHALL show, for every session in the course-grouped history, a
trash-icon delete control with the tooltip «Удалить диалог», SHALL ask the user to confirm the
deletion, and SHALL remove the session from the list after it is deleted. When the deleted session
is the one currently open, the panel SHALL leave the conversation view and return to the reloaded
history.

#### Scenario: Delete control in history
- **WHEN** the user opens the assistant history
- **THEN** every listed session shows a delete control

#### Scenario: Delete control is a trash icon with a tooltip
- **WHEN** the assistant history is shown
- **THEN** the delete control is drawn as a trash icon
- **AND** its tooltip and accessible name are «Удалить диалог»

#### Scenario: Delete control stays inside the session item
- **WHEN** a session has a long preview text
- **THEN** the delete control stays within the bounds of the history card
- **AND** the preview is truncated with an ellipsis instead of widening the row

#### Scenario: Deletion requires confirmation
- **WHEN** the user activates the delete control of a session
- **THEN** the panel asks for confirmation before deleting
- **AND** no request is sent when the user cancels

#### Scenario: History refreshed after deletion
- **WHEN** the user confirms the deletion and the server responds with success
- **THEN** the panel reloads the session list and the deleted session is not shown

#### Scenario: Open conversation closed after deletion
- **WHEN** the user deletes the session that is currently open in the panel
- **THEN** the panel shows the reloaded history instead of the deleted conversation

### Requirement: Download dialogue as Markdown or PDF

The assistant chat panel SHALL show, while a dialogue is open, Markdown and PDF download controls
at the bottom of the dialogue directly after the last message, using the session export endpoint
through the web proxy so that the browser saves the file. The controls SHALL follow the newest
message when the dialogue grows.

#### Scenario: Download controls shown in a dialogue
- **WHEN** the user opens a dialogue in the assistant panel
- **THEN** the download controls are shown at the bottom of the dialogue, after the last message, rather than in the panel header

#### Scenario: Download controls follow the newest message
- **WHEN** a new message is appended to the open dialogue
- **THEN** the download controls are moved after that message

#### Scenario: Download controls hidden in history
- **WHEN** the panel shows the session history rather than a dialogue
- **THEN** the download controls are not shown

#### Scenario: Download targets the open session
- **WHEN** the user opens session `N` and activates the Markdown download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=md` and saves the file

#### Scenario: PDF download
- **WHEN** the user opens session `N` and activates the PDF download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=pdf` and saves the file

### Requirement: Neutral assistant failure message

When processing a question fails, the assistant chat panel SHALL display the neutral message
«Произошла ошибка, попробуйте чуть позже.» and SHALL NOT display the technical failure description
stored for the job. The neutral message SHALL also be shown when the panel cannot reach the API.

#### Scenario: Failed job shown neutrally
- **WHEN** the polled job reaches the `failed` status
- **THEN** the panel shows «Произошла ошибка, попробуйте чуть позже.»
- **AND** the technical error text of the job is not rendered

#### Scenario: Network failure shown neutrally
- **WHEN** a request to the chat API fails with a network error
- **THEN** the panel shows «Произошла ошибка, попробуйте чуть позже.»

#### Scenario: Other panel messages unchanged
- **WHEN** the panel cannot create a session, cannot enqueue the question, or exhausts the polling window
- **THEN** the panel keeps its distinct messages for those situations

### Requirement: Clear chat history from the assistant panel

The assistant history panel SHALL show an «Очистить историю» control when the history is not
empty, SHALL ask the user to confirm before deleting, and SHALL delete through the web proxy the
sessions shown in the panel: all sessions on course list pages, or only the sessions of the
current course on a course page. After a successful deletion the panel SHALL reload the history
and show its empty state.

#### Scenario: Clear control is shown with history
- **WHEN** the assistant panel shows a non-empty history
- **THEN** the panel shows the «Очистить историю» control

#### Scenario: Clearing requires confirmation
- **WHEN** the user activates «Очистить историю»
- **THEN** the panel asks for confirmation
- **AND** no request is sent when the user cancels

#### Scenario: Clearing the whole history on course lists
- **WHEN** the user confirms clearing on `/courses` or `/my-courses`
- **THEN** the panel requests `DELETE /api/v1/chat/sessions` without a course filter
- **AND** the history becomes empty

#### Scenario: Clearing only the current course history
- **WHEN** the user confirms clearing on a course page with course id 10
- **THEN** the panel requests `DELETE /api/v1/chat/sessions?course_id=10`
- **AND** sessions of other courses remain in the user's history

#### Scenario: Clear control disappears after clearing
- **WHEN** the history becomes empty after a successful clear
- **THEN** the panel shows the empty state and no «Очистить историю» control

### Requirement: Confirmation modal for destructive chat actions

The assistant panel SHALL confirm clearing the whole history and deleting a single dialogue in an
in-panel modal dialog with a cancel control and a destructive confirm control instead of a native
browser confirm. The dialog SHALL close without performing the action when the user cancels, clicks
the backdrop or presses Escape, and SHALL perform the action only after the confirm control is
activated.

#### Scenario: Clearing history opens the modal
- **WHEN** the user activates «Очистить историю»
- **THEN** the assistant panel shows a modal dialog with the confirmation text, a cancel control and a confirm control
- **AND** no request is sent yet

#### Scenario: Cancel keeps the history
- **WHEN** the modal is open and the user activates the cancel control
- **THEN** the modal closes and the history stays unchanged

#### Scenario: Backdrop and Escape cancel the action
- **WHEN** the modal is open and the user clicks the backdrop or presses Escape
- **THEN** the modal closes and no request is sent

#### Scenario: Confirm clears the history
- **WHEN** the user activates the confirm control in the modal
- **THEN** the modal closes and the panel sends the delete request

#### Scenario: Single dialogue uses the same modal
- **WHEN** the user activates the delete control of one dialogue
- **THEN** the same modal dialog asks for confirmation before the request is sent

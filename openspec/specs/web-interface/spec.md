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

### Requirement: Floating RAG assistant widget

The web service SHALL render a pinned assistant control at the bottom-left of the course page and the step page and SHALL open a RAG chat panel overlaid on the right side of the page when the control is activated, without shifting the page content. The control and the panel SHALL NOT be rendered on the courses list, the administrator page, the login page, or the registration page.

#### Scenario: Assistant control visible on course and step pages

- **WHEN** an authenticated user requests the course page or a step page
- **THEN** the web service returns the page containing a fixed assistant control pinned at the bottom-left

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

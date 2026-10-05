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
The web service SHALL proxy requests under `/api/*` to the API, forwarding the request method, query string, body, and relevant headers (including the session cookie), and SHALL relay response cookies back to the browser.

#### Scenario: Request forwarded
- **WHEN** a client requests `/api/v1/...` from the web service
- **THEN** the web service forwards the request to the API and returns the upstream status, body, and headers

#### Scenario: Session cookie relayed
- **WHEN** the API sets or clears a session cookie in response to a proxied request
- **THEN** the web service relays the `Set-Cookie` header to the browser

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

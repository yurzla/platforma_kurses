# web-interface

## Purpose

Отдельный сервис визуализации: отдаёт HTML-страницы (вход, обучение, дашборд), проксирует запросы браузера к JSON API и пробрасывает cookie сессии, не храня состояние аутентификации сам.

## ADDED Requirements

### Requirement: HTML pages served by the web service
The web service SHALL serve the user-facing HTML pages: a login page, the learning pages, and the admin dashboard.

#### Scenario: Login page
- **WHEN** a client requests the login page
- **THEN** the web service returns an HTML page with a control to choose between the student and administrator roles

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

### Requirement: Role-based login dispatch
The web service SHALL dispatch the login form to the API endpoint matching the selected role and SHALL redirect to the role-appropriate landing page on success.

#### Scenario: Student login
- **WHEN** a client submits the login form with the student role and valid credentials
- **THEN** the web service authenticates against the student API endpoint and redirects to the courses page

#### Scenario: Administrator login
- **WHEN** a client submits the login form with the administrator role and valid credentials
- **THEN** the web service authenticates against the admin API endpoint and redirects to the dashboard

#### Scenario: Failed login
- **WHEN** a client submits invalid credentials
- **THEN** the web service re-renders the login page with an error and does not establish a session

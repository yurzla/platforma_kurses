## REMOVED Requirements

### Requirement: Optional admin access token
**Reason**: Доступ по единому токену заменяется входом по логину и паролю.
**Migration**: Задайте `ADMIN_USERNAME`/`ADMIN_PASSWORD` и входите через форму `/login`; `ADMIN_TOKEN` больше не поддерживается.

## ADDED Requirements

### Requirement: Admin login (username/password)
The system SHALL protect the dashboard and admin API with a username and password when both are configured, and SHALL leave them open when no credentials are configured.

#### Scenario: Login required and missing
- **WHEN** credentials are configured and a client calls the admin API without an authenticated session
- **THEN** the system responds with HTTP 401

#### Scenario: Successful login
- **WHEN** a client submits the correct username and password to the login form
- **THEN** the system establishes an authenticated session and serves the dashboard and admin API

#### Scenario: Invalid credentials
- **WHEN** a client submits an incorrect username or password
- **THEN** the system responds with HTTP 401 and does not establish a session

#### Scenario: No credentials configured
- **WHEN** no admin username/password are configured
- **THEN** the dashboard and admin API are accessible without login

### Requirement: Admin session and logout
The system SHALL keep the authenticated session in a signed, HttpOnly cookie and SHALL allow the operator to log out.

#### Scenario: Session persists
- **WHEN** a client logs in and then loads the dashboard or calls the admin API
- **THEN** the requests are served using the session cookie

#### Scenario: Logout
- **WHEN** an authenticated client calls the logout endpoint
- **THEN** the session is cleared and subsequent admin requests require login again

#### Scenario: HTML page without session
- **WHEN** an unauthenticated client requests the dashboard HTML page
- **THEN** the system redirects to the login page with a `next` parameter pointing back to the requested page

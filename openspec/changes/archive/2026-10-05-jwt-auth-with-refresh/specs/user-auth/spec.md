## MODIFIED Requirements

### Requirement: User login
The system SHALL authenticate any user (student, teacher, or administrator) by email and password against the `users` table and, on success, SHALL issue an access JWT and a refresh token delivered as httpOnly cookies.

#### Scenario: Valid credentials
- **WHEN** a client submits a registered user's email and correct password
- **THEN** the system sets `access_token` and `refresh_token` httpOnly cookies and reports the user's role, id, name, and email

#### Scenario: Administrator login
- **WHEN** a user whose role is `admin` submits correct credentials
- **THEN** the system issues an access JWT and a refresh token reporting role `admin`

#### Scenario: Invalid credentials
- **WHEN** a client submits an unknown email or an incorrect password
- **THEN** the system responds with HTTP 401 and does not issue tokens

#### Scenario: Logout
- **WHEN** an authenticated user logs out
- **THEN** the system revokes the presented refresh token, clears both auth cookies, and subsequent authenticated requests require login again

### Requirement: Self-registration
The system SHALL allow self-registration on the portal only with the role `student` or `teacher`, and SHALL NOT allow creating an `admin` account through registration.

#### Scenario: Register a student
- **WHEN** a visitor submits an unused email, a name, a password, and the `student` role
- **THEN** the system creates a user with role `student` and issues an access JWT and a refresh token

#### Scenario: Register a teacher
- **WHEN** a visitor submits an unused email, a name, a password, and the `teacher` role
- **THEN** the system creates a user with role `teacher` and issues an access JWT and a refresh token

#### Scenario: Administrator role rejected
- **WHEN** a visitor attempts to register with the role `admin`
- **THEN** the system rejects the request and does not create an administrator

#### Scenario: Duplicate email
- **WHEN** a visitor registers with an email that already exists
- **THEN** the system rejects the request and does not create a duplicate user

### Requirement: Current user
The system SHALL report the current authenticated user's identity and role on request, resolving the user from the access token and the database.

#### Scenario: Current user reported
- **WHEN** an authenticated user requests the current-user endpoint
- **THEN** the system reports the user's role, id, name, and email

#### Scenario: Anonymous
- **WHEN** an unauthenticated client requests the current-user endpoint
- **THEN** the system reports no role

## ADDED Requirements

### Requirement: Access and refresh tokens
The system SHALL issue a short-lived access JWT carrying the user identifier and expiry, and a longer-lived refresh token; the user's role SHALL be resolved from the database on each authenticated request. Authenticated endpoints SHALL accept the access token from the httpOnly cookie or an `Authorization: Bearer` header.

#### Scenario: Access token accepted
- **WHEN** a client presents a valid, unexpired access token
- **THEN** the system authenticates the request and resolves the current user

#### Scenario: Expired access token rejected
- **WHEN** a client presents an access token whose expiry has passed
- **THEN** the system responds with HTTP 401

#### Scenario: Tampered token rejected
- **WHEN** a client presents an access token with an invalid signature or type
- **THEN** the system responds with HTTP 401

#### Scenario: Role change reflected
- **WHEN** an administrator changes a user's role
- **THEN** subsequent requests with that user's existing access token use the new role

### Requirement: Token refresh and revocation
The system SHALL allow exchanging a valid refresh token for a new token pair, SHALL rotate the refresh token by revoking the previous one, and SHALL persist refresh tokens so they can be revoked.

#### Scenario: Refresh rotates tokens
- **WHEN** a client presents a valid refresh token to the refresh endpoint
- **THEN** the system revokes that refresh token and issues a new access token and refresh token

#### Scenario: Invalid refresh rejected
- **WHEN** a client presents an unknown, expired, or already revoked refresh token
- **THEN** the system responds with HTTP 401 and issues no tokens

#### Scenario: Reuse of rotated token
- **WHEN** a client presents a refresh token that was already rotated
- **THEN** the system revokes all of that user's refresh tokens and responds with HTTP 401

# user-auth Specification

## Purpose
Единая аутентификация пользователей по таблице `users`: вход и выход по email и паролю для всех ролей, определение текущего пользователя, самостоятельная регистрация с ролью `student` или `teacher` и хранение паролей в виде обратимого шифрования секретным ключом.

## Requirements

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

#### Scenario: Invalid access token rejected
- **WHEN** a client requests the current-user endpoint with an expired or invalid access token
- **THEN** the system responds with HTTP 401 so the client can refresh the token

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

### Requirement: Password encryption with a server key

The system SHALL store user passwords reversibly encrypted with the server key `PASSWORD_KEY` from the environment and SHALL verify a supplied password by decrypting the stored value. The key and the generated password file SHALL NOT be committed to the repository or baked into container images.

#### Scenario: Encryption round-trip

- **WHEN** a password is encrypted and later verified with the same password
- **THEN** verification succeeds; verification with a different password fails

#### Scenario: Tampered value rejected

- **WHEN** the stored encrypted value is modified or was encrypted with another key
- **THEN** verification fails

#### Scenario: Missing key

- **WHEN** a password operation runs without `PASSWORD_KEY`
- **THEN** the system fails with a clear configuration error instead of storing or accepting a password

#### Scenario: Legacy hashes rejected

- **WHEN** the stored value uses the old `scrypt` format
- **THEN** verification fails and the user must receive a new password through the reset procedure

### Requirement: Bulk password reset

The system SHALL provide a script that generates new random passwords for all existing users, stores them encrypted with `PASSWORD_KEY`, revokes active refresh tokens, and writes the logins and plaintext passwords to a git-ignored file readable only by the owner.

#### Scenario: Reset all users

- **WHEN** an operator runs the reset script with `PASSWORD_KEY` set
- **THEN** every user receives a new encrypted password and the script writes the login/password pairs to the configured file

#### Scenario: Missing key on reset

- **WHEN** the reset script runs without `PASSWORD_KEY`
- **THEN** it exits with a configuration error and changes no passwords

#### Scenario: Credentials file is not committed

- **WHEN** the reset script writes the credentials file
- **THEN** the file lives in a git-ignored directory with owner-only permissions

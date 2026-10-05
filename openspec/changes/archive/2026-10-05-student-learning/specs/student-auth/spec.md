# student-auth

## Purpose

Аутентификация студентов по учётным данным из таблицы `users`: вход, выход и определение текущего пользователя для доступа к учебному контенту.

## ADDED Requirements

### Requirement: Student login
The system SHALL authenticate a student by email and password against the `users` table and SHALL establish a session on success.

#### Scenario: Valid credentials
- **WHEN** a client submits a registered student's email and correct password
- **THEN** the system establishes an authenticated session and reports the student's role, id, name, and email

#### Scenario: Invalid credentials
- **WHEN** a client submits an unknown email or an incorrect password
- **THEN** the system responds with HTTP 401 and does not establish a session

#### Scenario: Non-student account
- **WHEN** a client submits credentials of a user whose role is not `student`
- **THEN** the system responds with HTTP 401

### Requirement: Student session and current user
The system SHALL store the authenticated student's identity in the signed session cookie and SHALL report the current user on request.

#### Scenario: Current user
- **WHEN** an authenticated student requests the current-user endpoint
- **THEN** the system reports role `student` with the student's id, name, and email

#### Scenario: Logout
- **WHEN** an authenticated student logs out
- **THEN** the session is cleared and subsequent student-only requests require login again

### Requirement: Password hashing
The system SHALL store student passwords as salted scrypt hashes and SHALL verify them without revealing the stored hash.

#### Scenario: Hash round-trip
- **WHEN** a password is hashed and later verified with the same password
- **THEN** verification succeeds; verification with a different password fails

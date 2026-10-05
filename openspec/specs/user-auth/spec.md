# user-auth Specification

## Purpose
Единая аутентификация пользователей по таблице `users`: вход и выход по email и паролю для всех ролей, определение текущего пользователя, самостоятельная регистрация с ролью `student` или `teacher` и хранение паролей в виде стойких хешей.

## Requirements

### Requirement: User login
The system SHALL authenticate any user (student, teacher, or administrator) by email and password against the `users` table and SHALL establish a single session on success.

#### Scenario: Valid credentials
- **WHEN** a client submits a registered user's email and correct password
- **THEN** the system establishes an authenticated session and reports the user's role, id, name, and email

#### Scenario: Administrator login
- **WHEN** a user whose role is `admin` submits correct credentials
- **THEN** the system establishes a session reporting role `admin`

#### Scenario: Invalid credentials
- **WHEN** a client submits an unknown email or an incorrect password
- **THEN** the system responds with HTTP 401 and does not establish a session

#### Scenario: Logout
- **WHEN** an authenticated user logs out
- **THEN** the session is cleared and subsequent authenticated requests require login again

### Requirement: Self-registration
The system SHALL allow self-registration on the portal only with the role `student` or `teacher`, and SHALL NOT allow creating an `admin` account through registration.

#### Scenario: Register a student
- **WHEN** a visitor submits an unused email, a name, a password, and the `student` role
- **THEN** the system creates a user with role `student` and establishes a session

#### Scenario: Register a teacher
- **WHEN** a visitor submits an unused email, a name, a password, and the `teacher` role
- **THEN** the system creates a user with role `teacher` and establishes a session

#### Scenario: Administrator role rejected
- **WHEN** a visitor attempts to register with the role `admin`
- **THEN** the system rejects the request and does not create an administrator

#### Scenario: Duplicate email
- **WHEN** a visitor registers with an email that already exists
- **THEN** the system rejects the request and does not create a duplicate user

### Requirement: Current user
The system SHALL report the current authenticated user's identity and role on request.

#### Scenario: Current user reported
- **WHEN** an authenticated user requests the current-user endpoint
- **THEN** the system reports the user's role, id, name, and email

#### Scenario: Anonymous
- **WHEN** an unauthenticated client requests the current-user endpoint
- **THEN** the system reports no role

### Requirement: Password hashing
The system SHALL store user passwords as salted scrypt hashes and SHALL verify them without revealing the stored hash.

#### Scenario: Hash round-trip
- **WHEN** a password is hashed and later verified with the same password
- **THEN** verification succeeds; verification with a different password fails

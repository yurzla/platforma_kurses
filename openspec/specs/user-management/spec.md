# user-management Specification

## Purpose
Администрирование пользователей: просмотр списка с поиском и пагинацией и назначение ролей (`student`/`teacher`/`admin`) администратором.

## Requirements

### Requirement: List users
The system SHALL allow an administrator to list users with optional text search and pagination.

#### Scenario: Users listed
- **WHEN** an administrator requests the user list with a limit and offset
- **THEN** the system returns the matching users (id, email, name, role, created_at) and the total count

#### Scenario: Search by email or name
- **WHEN** an administrator requests the user list with a search term
- **THEN** the system returns only users whose email or name matches the term

#### Scenario: Administrator required
- **WHEN** a client without the `admin` role requests the user list
- **THEN** the system responds with HTTP 401 or 403

### Requirement: Assign roles
The system SHALL allow an administrator to change another user's role to any of `student`, `teacher`, or `admin`.

#### Scenario: Role changed
- **WHEN** an administrator changes another user's role to a supported value
- **THEN** the system persists the new role and returns the updated user

#### Scenario: Unsupported role
- **WHEN** an administrator submits a role outside `student`/`teacher`/`admin`
- **THEN** the system rejects the request

#### Scenario: Own role change forbidden
- **WHEN** an administrator attempts to change their own role
- **THEN** the system rejects the request

#### Scenario: Unknown user
- **WHEN** an administrator changes the role of a non-existent user
- **THEN** the system responds with HTTP 404

#### Scenario: Administrator role granted
- **WHEN** an administrator grants the `admin` role to another user
- **THEN** that user gains administrator access on subsequent requests

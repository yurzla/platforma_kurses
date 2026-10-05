## MODIFIED Requirements

### Requirement: Create chat session
The system SHALL allow creating a chat session bound to a user and a course, and SHALL return a unique session identifier. When the caller is an authenticated student, the system SHALL bind the session to that student regardless of the supplied user identifier.

#### Scenario: Session created
- **WHEN** a client requests a new chat session for an existing user and course
- **THEN** the system responds with HTTP 201 and a session identifier
- **AND** the session is persisted with the given user and course

#### Scenario: Unknown user or course
- **WHEN** a client requests a session for a non-existent user or course
- **THEN** the system responds with HTTP 404 and does not create a session

#### Scenario: Authenticated student
- **WHEN** an authenticated student requests a new chat session and supplies no user identifier
- **THEN** the system binds the session to the authenticated student

#### Scenario: No user and no session
- **WHEN** a client requests a new chat session without an authenticated student and without a user identifier
- **THEN** the system responds with HTTP 401

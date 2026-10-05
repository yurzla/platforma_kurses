## MODIFIED Requirements

### Requirement: Create chat session
The system SHALL allow an authenticated user to create a chat session bound to that user and a course, and SHALL return a unique session identifier. The session SHALL always be bound to the authenticated user.

#### Scenario: Session created
- **WHEN** an authenticated user requests a new chat session for an existing course
- **THEN** the system responds with HTTP 201 and a session identifier
- **AND** the session is persisted with the authenticated user and the course

#### Scenario: Unknown user or course
- **WHEN** an authenticated user requests a session for a non-existent course
- **THEN** the system responds with HTTP 404 and does not create a session

#### Scenario: Authenticated student
- **WHEN** an authenticated student requests a new chat session and supplies no user identifier
- **THEN** the system binds the session to the authenticated student

#### Scenario: No user and no session
- **WHEN** a client requests a new chat session without an authenticated user
- **THEN** the system responds with HTTP 401

### Requirement: Retrieve message history
The system SHALL return the messages of a chat session in chronological order, limited to the most recent N messages when a limit is provided, and SHALL only return history to the session's owner or an administrator.

#### Scenario: History returned in order
- **WHEN** the session's owner requests the history of an existing session with a limit
- **THEN** the system returns at most `limit` messages ordered from oldest to newest

#### Scenario: Unknown session
- **WHEN** a client requests history for a non-existent session
- **THEN** the system responds with HTTP 404

#### Scenario: Foreign session forbidden
- **WHEN** an authenticated user requests history for a session owned by another user
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous rejected
- **WHEN** an unauthenticated client requests message history
- **THEN** the system responds with HTTP 401

## MODIFIED Requirements

### Requirement: Create chat session
The system SHALL allow an authenticated user to create a chat session bound to that user and, optionally, a course, and SHALL return a unique session identifier. The session SHALL always be bound to the authenticated user.

#### Scenario: Session created
- **WHEN** an authenticated user requests a new chat session for an existing course
- **THEN** the system responds with HTTP 201 and a session identifier
- **AND** the session is persisted with the authenticated user and the course

#### Scenario: Session created without a course
- **WHEN** an authenticated user requests a new chat session without specifying a course
- **THEN** the system responds with HTTP 201 and a session identifier not bound to any single course

#### Scenario: Unknown user or course
- **WHEN** an authenticated user requests a session for a non-existent course
- **THEN** the system responds with HTTP 404 and does not create a session

#### Scenario: Authenticated student
- **WHEN** an authenticated student requests a new chat session and supplies no user identifier
- **THEN** the system binds the session to the authenticated student

#### Scenario: No user and no session
- **WHEN** a client requests a new chat session without an authenticated user
- **THEN** the system responds with HTTP 401

### Requirement: Course-scoped RAG answer
When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), build context from those chunks, and generate an answer with the configured LLM. The system SHALL persist the original user question and the assistant answer, and SHALL record the chunk identifiers used as sources.

#### Scenario: Answer with sources
- **WHEN** a question is processed for a session whose course has matching material
- **THEN** an assistant answer is generated from the retrieved course chunks
- **AND** the answer is persisted together with the chunk identifiers used as sources

#### Scenario: Answer without a course
- **WHEN** a question is processed for a session not bound to a course and matching material exists in any course
- **THEN** an assistant answer is generated from the retrieved chunks across all courses

#### Scenario: No matching material
- **WHEN** a question is processed and no course chunks are retrieved
- **THEN** the system returns a clear "no material found" answer without calling the LLM
- **AND** the exchange is still persisted

#### Scenario: Retrieval restricted to course
- **WHEN** the same question is asked in sessions of two different courses
- **THEN** each answer is generated only from chunks belonging to its own course

## ADDED Requirements

### Requirement: List chat sessions

The system SHALL return the authenticated user's chat sessions, most recent first, each with its course reference, course title, start time and a preview of the last message, and SHALL return only the sessions owned by that user.

#### Scenario: Own sessions listed

- **WHEN** an authenticated user requests their chat sessions
- **THEN** the system returns the user's sessions ordered from most recent to oldest, each with the course title and last-message preview

#### Scenario: Only own sessions

- **WHEN** an authenticated user requests their chat sessions
- **THEN** sessions owned by other users are not returned

#### Scenario: Anonymous rejected

- **WHEN** an unauthenticated client requests the chat session list
- **THEN** the system responds with HTTP 401

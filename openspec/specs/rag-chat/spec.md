# rag-chat

## Purpose

Provides course-scoped conversational Q&A: students create chat sessions, submit questions, and receive answers grounded in the current course materials, with conversation history and cited sources.

## Requirements

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

### Requirement: Course-scoped RAG answer
When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), and generate an answer with the configured LLM. For a session not bound to a course the system SHALL also include the platform course catalog (title and short description of each published course, marking courses the user is enrolled in) in the prompt and SHALL instruct the model to recommend only courses present in that catalog. The system SHALL persist the original user question and the assistant answer, and SHALL record the chunk identifiers used as sources.

#### Scenario: Answer with sources
- **WHEN** a question is processed for a session whose course has matching material
- **THEN** an assistant answer is generated from the retrieved course chunks
- **AND** the answer is persisted together with the chunk identifiers used as sources

#### Scenario: Answer without a course
- **WHEN** a question is processed for a session not bound to a course and matching material exists in any course
- **THEN** an assistant answer is generated from the retrieved chunks across all courses

#### Scenario: Course recommendation in a global session
- **WHEN** a question asks which course to take and the session is not bound to a course
- **THEN** the generated answer recommends courses taken from the platform catalog
- **AND** courses the user is enrolled in are marked as such in the prompt

#### Scenario: No matching material
- **WHEN** a question is processed, no course chunks are retrieved, and the session is bound to a course
- **THEN** the system returns a clear "no material found" answer without calling the LLM
- **AND** the exchange is still persisted

#### Scenario: No matching material in a global session
- **WHEN** a question is processed for a session not bound to a course and no course chunks are retrieved but the platform has published courses
- **THEN** the system still generates an answer using the platform course catalog

#### Scenario: Retrieval restricted to course
- **WHEN** the same question is asked in sessions of two different courses
- **THEN** each answer is generated only from chunks belonging to its own course

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

### Requirement: Markdown-formatted answers

The system SHALL instruct the language model to format assistant answers in Markdown, using bold
for emphasis and fenced code blocks for multi-line code (inline code for short fragments), so that
the web panel can render the formatting.

#### Scenario: Answer formatted in Markdown
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use Markdown bold and fenced code blocks

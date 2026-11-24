## ADDED Requirements

### Requirement: Delete chat session

The system SHALL allow the session's owner or an administrator to permanently delete a chat
session together with all its messages and question jobs, and SHALL respond with HTTP 204 on
success. Deleting a session SHALL NOT affect other sessions, other jobs, or course materials.

#### Scenario: Owner deletes a session
- **WHEN** the session's owner requests deletion of an existing session
- **THEN** the system responds with HTTP 204
- **AND** the session and its messages are no longer returned by the chat endpoints

#### Scenario: Administrator deletes a foreign session
- **WHEN** an authenticated administrator requests deletion of a session owned by another user
- **THEN** the system responds with HTTP 204 and the session is deleted

#### Scenario: Foreign session forbidden
- **WHEN** an authenticated user requests deletion of a session owned by another user and is not an administrator
- **THEN** the system responds with HTTP 403 and the session remains

#### Scenario: Unknown session
- **WHEN** a client requests deletion of a non-existent session
- **THEN** the system responds with HTTP 404

#### Scenario: Anonymous rejected
- **WHEN** an unauthenticated client requests deletion of a session
- **THEN** the system responds with HTTP 401 and nothing is deleted

#### Scenario: Session jobs removed with the session
- **WHEN** a session that has question jobs is deleted
- **THEN** the jobs belonging to that session are deleted as well
- **AND** jobs of other sessions are kept

### Requirement: Export chat session
The system SHALL let the session's owner or an administrator download the dialogue of a chat
session as an attached Markdown (`format=md`) or PDF (`format=pdf`) file, and SHALL reject any other
format with HTTP 400. The exported document SHALL contain the session start date, the dialogue
messages in chronological order with their roles, and the sources of assistant answers when present.

#### Scenario: Markdown export
- **WHEN** the session's owner requests the dialogue export with `format=md`
- **THEN** the system responds with HTTP 200, a Markdown content type and a `Content-Disposition` attachment header
- **AND** the file name has the form `dialog-<session_id>-<YYYY-MM-DD>.md`
- **AND** the body contains the course title when the session is bound to a course and every message in chronological order with its role

#### Scenario: PDF export
- **WHEN** the session's owner requests the dialogue export with `format=pdf`
- **THEN** the system responds with HTTP 200, a PDF content type and a `Content-Disposition` attachment header
- **AND** the file name has the form `dialog-<session_id>-<YYYY-MM-DD>.pdf`
- **AND** the body is a PDF document containing the dialogue text, including Cyrillic characters

#### Scenario: Assistant sources included
- **WHEN** an assistant message of the exported session references sources
- **THEN** the exported document lists those sources for that answer

#### Scenario: Unsupported format
- **WHEN** a client requests the export with a format other than `md` or `pdf`
- **THEN** the system responds with HTTP 400 and does not produce a file

#### Scenario: Foreign session forbidden
- **WHEN** an authenticated user requests the export of a session owned by another user and is not an administrator
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous rejected
- **WHEN** an unauthenticated client requests the export of a session
- **THEN** the system responds with HTTP 401

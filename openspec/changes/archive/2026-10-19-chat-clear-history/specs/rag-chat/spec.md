## ADDED Requirements

### Requirement: Clear chat history

The API SHALL let an authenticated user delete all of their chat sessions with a single
`DELETE /api/v1/chat/sessions` request, and SHALL accept an optional `course_id` query parameter
that limits the deletion to the sessions of that course. Question jobs of the deleted sessions
SHALL be removed in the same operation, the response SHALL be HTTP 204 without a body, and
sessions of other users SHALL never be deleted.

#### Scenario: Delete all sessions of the user
- **WHEN** an authenticated user calls `DELETE /api/v1/chat/sessions`
- **THEN** the system responds with HTTP 204
- **AND** every chat session of that user, its messages and its question jobs are deleted
- **AND** sessions of other users remain unchanged

#### Scenario: Delete sessions of one course
- **WHEN** an authenticated user calls `DELETE /api/v1/chat/sessions?course_id=10`
- **THEN** only the user's sessions bound to course 10 are deleted
- **AND** the user's sessions of other courses remain

#### Scenario: Clearing history requires authentication
- **WHEN** an unauthenticated request calls `DELETE /api/v1/chat/sessions`
- **THEN** the system responds with HTTP 401

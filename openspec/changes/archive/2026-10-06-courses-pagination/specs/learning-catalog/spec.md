## MODIFIED Requirements

### Requirement: Course catalog
The system SHALL expose the list of published courses with lesson/step counts and, for the authenticated user, enrollment and progress information. The list SHALL be paginated: the response SHALL be an object with `items`, `total`, `limit`, and `offset`, controlled by the `limit` (1..200) and `offset` query parameters, and SHALL preserve the enrollment filter when requested.

#### Scenario: Courses listed
- **WHEN** an authenticated user requests the course list
- **THEN** the system returns an object with the published courses in `items`, their counts and the user's progress, plus `total`, `limit`, and `offset`

#### Scenario: Authentication required
- **WHEN** an unauthenticated client requests the course catalog
- **THEN** the system responds with HTTP 401

#### Scenario: Pagination window
- **WHEN** an authenticated user requests the course list with `limit` and `offset`
- **THEN** the system returns at most `limit` courses starting from `offset` and reports the full `total`

#### Scenario: Enrolled filter combined with pagination
- **WHEN** an authenticated user requests the course list with `enrolled=true`
- **THEN** the page contains only courses with the user's enrollment and `total` counts only those courses

## ADDED Requirements

### Requirement: Filter courses by enrollment

The course catalog SHALL support returning only the courses in which the authenticated user has enrollment when the list endpoint is called with the `enrolled=true` filter, while returning all published courses when the filter is absent.

#### Scenario: Enrolled filter applied

- **WHEN** an authenticated user requests the course list with `enrolled=true`
- **THEN** the system returns only the published courses that have an enrollment of that user

#### Scenario: No filter returns full catalog

- **WHEN** an authenticated user requests the course list without the enrolled filter
- **THEN** the system returns all published courses with the user's enrollment and progress information

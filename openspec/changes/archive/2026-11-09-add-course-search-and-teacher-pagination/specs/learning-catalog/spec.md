# learning-catalog delta

## ADDED Requirements

### Requirement: Course search

The course list endpoint SHALL accept an optional `search` query parameter. Search SHALL be case-insensitive, SHALL match the course title or description, SHALL combine with the `enrolled` filter, and SHALL be applied before pagination so `total` reflects the number of matches.

#### Scenario: Search by title

- **WHEN** an authenticated user requests the course list with `search=python`
- **THEN** the response contains only courses whose title contains `python` in any case

#### Scenario: Search by description

- **WHEN** an authenticated user requests the course list with a term present only in a course description
- **THEN** that course is returned

#### Scenario: Search combined with enrollment

- **WHEN** an authenticated user requests the course list with `search` and `enrolled=true`
- **THEN** the response contains only enrolled courses matching the search term, and `total` counts only those courses

#### Scenario: No matches

- **WHEN** no published course matches the search term
- **THEN** `items` is empty and `total` is zero

#### Scenario: Pagination counts matches

- **WHEN** matching courses span more than one page with `limit` and `offset`
- **THEN** the page contains at most `limit` matching courses and `total` reports all matches

#### Scenario: Literal wildcard characters

- **WHEN** the search term contains `%`, `_`, or `\`
- **THEN** those characters are matched literally rather than as SQL wildcards

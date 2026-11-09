# web-interface delta

## ADDED Requirements

### Requirement: Course search on list pages

The web service SHALL render a search form on the `/courses` and `/my-courses` pages. The form SHALL submit the `search` query parameter, SHALL keep the current value in the input, and SHALL preserve the search term in pagination links and out-of-range page redirects. An empty result SHALL show a message specific to the active search.

#### Scenario: Search form on both lists

- **WHEN** an authenticated user opens `/courses` or `/my-courses`
- **THEN** the page shows a search form targeting the current list

#### Scenario: Filtered cards

- **WHEN** the user submits a search term
- **THEN** only matching courses are rendered, the input keeps the term, and pagination links include it

#### Scenario: Clear search

- **WHEN** a search term is active
- **THEN** the page offers a control that returns to the unfiltered list

#### Scenario: No search results

- **WHEN** the search term matches no courses on the current list
- **THEN** the page shows a no-results message instead of the generic empty state

### Requirement: Teacher page pagination and search

The web service SHALL paginate the `/teacher` course list to at most 10 courses per page, SHALL render page navigation when more than one page exists, SHALL render a search form over the teacher's own courses, and SHALL preserve the search term in pagination links.

#### Scenario: Paginated teacher courses

- **WHEN** a teacher has more than 10 courses
- **THEN** `/teacher` shows at most 10 course cards and page navigation

#### Scenario: Teacher search

- **WHEN** a teacher submits a search term on `/teacher`
- **THEN** only the teacher's matching courses are shown and the term remains in the input

#### Scenario: Teacher search in pagination

- **WHEN** a filtered teacher list spans several pages
- **THEN** pagination links keep the search term

#### Scenario: Teacher empty states

- **WHEN** the teacher has no courses or the search has no matches
- **THEN** the page shows the corresponding empty-state message and, when searching, a reset control

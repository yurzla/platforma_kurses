## ADDED Requirements

### Requirement: Course list pagination and layout

The web service SHALL show the course lists (`/courses` and `/my-courses`) as pages of at most 10 courses, SHALL render page navigation (previous/next controls and page numbers) when more than one page exists, and SHALL lay the course cards out in two columns on wide screens and a single column on narrow screens.

#### Scenario: At most ten courses per page

- **WHEN** an authenticated user opens a course list page
- **THEN** the page shows at most 10 course cards

#### Scenario: Page navigation shown for multiple pages

- **WHEN** the course list has more courses than fit on one page
- **THEN** the page shows previous/next controls and page numbers linking to the other pages

#### Scenario: Requesting a specific page

- **WHEN** the user opens a course list page with the `page` parameter
- **THEN** the page shows the corresponding slice of courses and highlights the current page number

#### Scenario: No navigation for a single page

- **WHEN** the course list fits on a single page
- **THEN** the page shows no page navigation controls

#### Scenario: Two-column card grid

- **WHEN** a course list page is rendered on a wide screen
- **THEN** the course cards are arranged in two columns, collapsing to a single column on narrow screens

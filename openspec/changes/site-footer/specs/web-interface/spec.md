## ADDED Requirements

### Requirement: Site footer

Every page served by the web service SHALL render a common footer containing the project name
«Courses Assistant» with the same robot logo used in the top navigation, a note that the project is
an educational project created as part of completing a course, and the current year.

#### Scenario: Footer rendered on a page

- **WHEN** a user opens any page of the web interface
- **THEN** the page contains a footer with the «Courses Assistant» name, the robot logo, the
  educational-project note, and the current year

#### Scenario: Footer on authentication pages

- **WHEN** an unauthenticated user opens the login or registration page
- **THEN** the page contains the same footer

#### Scenario: Footer visible on short pages

- **WHEN** the page content is shorter than the viewport
- **THEN** the footer stays at the bottom of the viewport instead of floating in the middle

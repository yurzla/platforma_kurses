# web-interface delta

## ADDED Requirements

### Requirement: Icon controls and clean navigation

The web interface SHALL load Bootstrap Icons locally and SHALL use icon-only controls for the assistant toggle and the course search submit button while keeping accessible names. The top navigation SHALL show the product name with a robot icon and SHALL NOT show the "· обучение" suffix. Action links styled as buttons SHALL NOT be underlined.

#### Scenario: Top navigation brand

- **WHEN** an authenticated page is rendered
- **THEN** the top bar shows the product name with a robot icon and no "· обучение" suffix

#### Scenario: Assistant toggle

- **WHEN** the assistant is available on a page
- **THEN** its toggle shows a robot icon and exposes the accessible name "Ассистент"

#### Scenario: Search submit

- **WHEN** the course search form is rendered
- **THEN** the submit control shows only a search icon and exposes the accessible name "Найти"

#### Scenario: Button links are not underlined

- **WHEN** a page renders a link styled as a button, such as the step navigation or the search reset
- **THEN** the link text is not underlined

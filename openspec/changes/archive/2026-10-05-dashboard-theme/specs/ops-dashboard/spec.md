## MODIFIED Requirements

### Requirement: Dashboard page
The system SHALL serve a human-readable dashboard page presenting jobs, dead-letter entries, and stream metrics with automatic refresh, and SHALL provide a control to switch between light and dark themes.

#### Scenario: Dashboard rendered
- **WHEN** a client requests the dashboard page
- **THEN** the system returns an HTML page with sections for jobs, DLQ, and streams and the assets to refresh them

#### Scenario: Theme control present
- **WHEN** the dashboard page is served
- **THEN** it includes a theme toggle control

## ADDED Requirements

### Requirement: Theme switching
The system SHALL allow switching between light and dark themes on the dashboard and login pages, and SHALL remember the operator's choice.

#### Scenario: Toggle theme
- **WHEN** the operator activates the theme toggle
- **THEN** the interface switches between light and dark themes immediately

#### Scenario: Preference persists
- **WHEN** the operator has chosen a theme and reloads the page or opens another page of the interface
- **THEN** the previously chosen theme is applied without a flash of the other theme

#### Scenario: Default to system preference
- **WHEN** no theme has been chosen yet
- **THEN** the initial theme follows the operating system's color-scheme preference

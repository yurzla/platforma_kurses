## ADDED Requirements

### Requirement: Assistant drawer placement and dismissal

The assistant chat panel SHALL be rendered as a floating, rounded window positioned below the top
navigation bar so that it does not cover the navigation bar, and SHALL close when the user clicks
outside the panel. Clicking inside the panel SHALL NOT close it.

#### Scenario: Panel below the navigation bar
- **WHEN** the user opens the assistant panel
- **THEN** the panel is shown below the top navigation bar without covering it

#### Scenario: Rounded panel
- **WHEN** the assistant panel is visible
- **THEN** it is drawn as a rounded floating window

#### Scenario: Outside click closes the panel
- **WHEN** the assistant panel is open and the user clicks outside the panel
- **THEN** the panel closes

#### Scenario: Inside click keeps the panel open
- **WHEN** the assistant panel is open and the user clicks inside the panel
- **THEN** the panel stays open

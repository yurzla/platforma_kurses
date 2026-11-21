# student-preferences Specification

## Purpose

Позволить студенту хранить предпочтения для персонализации обучения.

## ADDED Requirements

### Requirement: Student learning preferences

The system SHALL let an authenticated user view and save their own interests, learning goals and
preferred course level. The system SHALL persist these values in the one-to-one
`user_learning_preferences` record for that user and SHALL not accept a user identifier from the
client.

#### Scenario: Empty preferences form

- **WHEN** an authenticated user opens «Моё обучение» without saved preferences
- **THEN** the page shows an «Обо мне» section with empty interests and goals fields and an
  unselected level

#### Scenario: Preferences saved

- **WHEN** an authenticated user submits interests, goals and a preferred level
- **THEN** the system creates or updates that user's preferences record
- **AND** the page subsequently shows the saved values

#### Scenario: Vertical and expanding text fields

- **WHEN** an authenticated user opens or fills the preferences form
- **THEN** interests, goals and preferred level are arranged in one vertical column
- **AND** each text field expands to fit its content without an inner scrollbar

#### Scenario: Preferences require authentication

- **WHEN** an unauthenticated client requests or updates preferences
- **THEN** the API responds with HTTP 401

#### Scenario: Invalid level rejected

- **WHEN** a user submits a level outside the supported choices
- **THEN** the API responds with HTTP 422 and leaves existing preferences unchanged

### Requirement: Preferences inform global course recommendations

When an authenticated user asks for a course recommendation in a global assistant session, the
system SHALL include their non-empty saved interests, goals and preferred level in the temporary
semantic search text together with the question. It SHALL not persist a separate preference
embedding.

#### Scenario: Populated preferences guide recommendations

- **WHEN** a user with saved preferences asks for a global course recommendation
- **THEN** the recommendation search embedding includes the question and saved preferences

#### Scenario: Empty preferences preserve current recommendations

- **WHEN** a user without saved preferences asks for a global course recommendation
- **THEN** the recommendation search embedding is based only on the question and its expansion

#### Scenario: Completed courses inform but are not recommended

- **WHEN** a user with completed courses asks for a global course recommendation
- **THEN** the search text includes each completed course's title and description
- **AND** completed courses are excluded from the recommendation candidates
- **AND** courses in progress remain eligible candidates

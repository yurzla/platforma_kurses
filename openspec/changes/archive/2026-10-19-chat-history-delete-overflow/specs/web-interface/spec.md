## MODIFIED Requirements

### Requirement: Delete chat session from history

The assistant chat panel SHALL show, for every session in the course-grouped history, a
trash-icon delete control with the tooltip «Удалить диалог», SHALL ask the user to confirm the
deletion, and SHALL remove the session from the list after it is deleted. When the deleted session
is the one currently open, the panel SHALL leave the conversation view and return to the reloaded
history.

#### Scenario: Delete control in history
- **WHEN** the user opens the assistant history
- **THEN** every listed session shows a delete control

#### Scenario: Delete control is a trash icon with a tooltip
- **WHEN** the assistant history is shown
- **THEN** the delete control is drawn as a trash icon
- **AND** its tooltip and accessible name are «Удалить диалог»

#### Scenario: Delete control stays inside the session item
- **WHEN** a session has a long preview text
- **THEN** the delete control stays within the bounds of the history card
- **AND** the preview is truncated with an ellipsis instead of widening the row

#### Scenario: Deletion requires confirmation
- **WHEN** the user activates the delete control of a session
- **THEN** the panel asks for confirmation before deleting
- **AND** no request is sent when the user cancels

#### Scenario: History refreshed after deletion
- **WHEN** the user confirms the deletion and the server responds with success
- **THEN** the panel reloads the session list and the deleted session is not shown

#### Scenario: Open conversation closed after deletion
- **WHEN** the user deletes the session that is currently open in the panel
- **THEN** the panel shows the reloaded history instead of the deleted conversation

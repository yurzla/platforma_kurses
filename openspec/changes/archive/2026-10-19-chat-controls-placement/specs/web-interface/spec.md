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

### Requirement: Download dialogue as Markdown or PDF

The assistant chat panel SHALL show, while a dialogue is open, Markdown and PDF download controls
at the bottom of the dialogue directly after the last message, using the session export endpoint
through the web proxy so that the browser saves the file. The controls SHALL follow the newest
message when the dialogue grows.

#### Scenario: Download controls shown in a dialogue
- **WHEN** the user opens a dialogue in the assistant panel
- **THEN** the download controls are shown at the bottom of the dialogue, after the last message, rather than in the panel header

#### Scenario: Download controls follow the newest message
- **WHEN** a new message is appended to the open dialogue
- **THEN** the download controls are moved after that message

#### Scenario: Download controls hidden in history
- **WHEN** the panel shows the session history rather than a dialogue
- **THEN** the download controls are not shown

#### Scenario: Download targets the open session
- **WHEN** the user opens session `N` and activates the Markdown download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=md` and saves the file

#### Scenario: PDF download
- **WHEN** the user opens session `N` and activates the PDF download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=pdf` and saves the file

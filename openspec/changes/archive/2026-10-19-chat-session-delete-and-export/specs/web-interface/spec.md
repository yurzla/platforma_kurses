## ADDED Requirements

### Requirement: Delete chat session from history

The assistant chat panel SHALL show a delete control for every session in the course-grouped
history, SHALL ask the user to confirm the deletion, and SHALL remove the session from the list
after it is deleted. When the deleted session is the one currently open, the panel SHALL leave the
conversation view and return to the reloaded history.

#### Scenario: Delete control in history
- **WHEN** the user opens the assistant history
- **THEN** every listed session shows a delete control

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

The assistant chat panel SHALL offer, while a dialogue is open, controls to download that dialogue
as a Markdown file and as a PDF file, using the session export endpoint through the web proxy so
that the browser saves the file.

#### Scenario: Download controls shown in a dialogue
- **WHEN** the user opens a dialogue in the assistant panel
- **THEN** the panel shows a control to download the dialogue as Markdown and a control to download it as PDF

#### Scenario: Download controls hidden in history
- **WHEN** the panel shows the session history rather than a dialogue
- **THEN** the download controls are not shown

#### Scenario: Download targets the open session
- **WHEN** the user opens session `N` and activates the Markdown download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=md` and saves the file

#### Scenario: PDF download
- **WHEN** the user opens session `N` and activates the PDF download control
- **THEN** the browser requests `/api/v1/chat/sessions/N/export?format=pdf` and saves the file

### Requirement: Neutral assistant failure message

When processing a question fails, the assistant chat panel SHALL display the neutral message
«Произошла ошибка, попробуйте чуть позже.» and SHALL NOT display the technical failure description
stored for the job. The neutral message SHALL also be shown when the panel cannot reach the API.

#### Scenario: Failed job shown neutrally
- **WHEN** the polled job reaches the `failed` status
- **THEN** the panel shows «Произошла ошибка, попробуйте чуть позже.»
- **AND** the technical error text of the job is not rendered

#### Scenario: Network failure shown neutrally
- **WHEN** a request to the chat API fails with a network error
- **THEN** the panel shows «Произошла ошибка, попробуйте чуть позже.»

#### Scenario: Other panel messages unchanged
- **WHEN** the panel cannot create a session, cannot enqueue the question, or exhausts the polling window
- **THEN** the panel keeps its distinct messages for those situations

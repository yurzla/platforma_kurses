## ADDED Requirements

### Requirement: Clear chat history from the assistant panel

The assistant history panel SHALL show an «Очистить историю» control when the history is not
empty, SHALL ask the user to confirm before deleting, and SHALL delete through the web proxy the
sessions shown in the panel: all sessions on course list pages, or only the sessions of the
current course on a course page. After a successful deletion the panel SHALL reload the history
and show its empty state.

#### Scenario: Clear control is shown with history
- **WHEN** the assistant panel shows a non-empty history
- **THEN** the panel shows the «Очистить историю» control

#### Scenario: Clearing requires confirmation
- **WHEN** the user activates «Очистить историю»
- **THEN** the panel asks for confirmation
- **AND** no request is sent when the user cancels

#### Scenario: Clearing the whole history on course lists
- **WHEN** the user confirms clearing on `/courses` or `/my-courses`
- **THEN** the panel requests `DELETE /api/v1/chat/sessions` without a course filter
- **AND** the history becomes empty

#### Scenario: Clearing only the current course history
- **WHEN** the user confirms clearing on a course page with course id 10
- **THEN** the panel requests `DELETE /api/v1/chat/sessions?course_id=10`
- **AND** sessions of other courses remain in the user's history

#### Scenario: Clear control disappears after clearing
- **WHEN** the history becomes empty after a successful clear
- **THEN** the panel shows the empty state and no «Очистить историю» control

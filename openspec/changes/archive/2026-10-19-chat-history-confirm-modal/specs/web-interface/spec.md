## ADDED Requirements

### Requirement: Confirmation modal for destructive chat actions

The assistant panel SHALL confirm clearing the whole history and deleting a single dialogue in an
in-panel modal dialog with a cancel control and a destructive confirm control instead of a native
browser confirm. The dialog SHALL close without performing the action when the user cancels, clicks
the backdrop or presses Escape, and SHALL perform the action only after the confirm control is
activated.

#### Scenario: Clearing history opens the modal
- **WHEN** the user activates «Очистить историю»
- **THEN** the assistant panel shows a modal dialog with the confirmation text, a cancel control and a confirm control
- **AND** no request is sent yet

#### Scenario: Cancel keeps the history
- **WHEN** the modal is open and the user activates the cancel control
- **THEN** the modal closes and the history stays unchanged

#### Scenario: Backdrop and Escape cancel the action
- **WHEN** the modal is open and the user clicks the backdrop or presses Escape
- **THEN** the modal closes and no request is sent

#### Scenario: Confirm clears the history
- **WHEN** the user activates the confirm control in the modal
- **THEN** the modal closes and the panel sends the delete request

#### Scenario: Single dialogue uses the same modal
- **WHEN** the user activates the delete control of one dialogue
- **THEN** the same modal dialog asks for confirmation before the request is sent

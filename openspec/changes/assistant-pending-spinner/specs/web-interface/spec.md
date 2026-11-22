## ADDED Requirements

### Requirement: Pending answer indicator

While the assistant panel is waiting for a generated answer, it SHALL show a spinning loading
indicator to the left of the «Ассистент отвечает…» text, vertically centered relative to that text,
and SHALL remove the indicator together with the placeholder when the answer, an error, or a
timeout is shown.

#### Scenario: Indicator shown while waiting

- **WHEN** the user submits a question and the panel is waiting for the job to complete
- **THEN** the panel shows a spinning indicator to the left of the «Ассистент отвечает…» text

#### Scenario: Indicator centered with text

- **WHEN** the pending indicator and its text are shown
- **THEN** the indicator is vertically centered relative to the text on the same line

#### Scenario: Indicator cleared with the answer

- **WHEN** the answer, an error, or a timeout replaces the pending placeholder
- **THEN** the indicator is removed and only the resulting message remains

# learning-catalog delta

## ADDED Requirements

### Requirement: Markdown step bodies

The step body SHALL be rendered as Markdown using CommonMark semantics with single line breaks preserved. Bodies that contain block-level HTML SHALL be rendered as raw HTML so imported content keeps its appearance. The rendered body SHALL be inserted into the step page without additional escaping.

#### Scenario: Markdown emphasis and links

- **WHEN** a step body contains `**bold**`, `*italic*`, or `[text](https://example.com)`
- **THEN** the step page renders strong, emphasis, and link elements respectively

#### Scenario: Markdown lists and code

- **WHEN** a step body contains a Markdown list or fenced code block
- **THEN** the step page renders the corresponding list or code markup

#### Scenario: Single line breaks preserved

- **WHEN** a Markdown step body contains a single line break
- **THEN** the step page renders a line break at that position

#### Scenario: Legacy HTML preserved

- **WHEN** a step body contains block-level HTML such as `<p>` or `<iframe>`
- **THEN** the step page renders that HTML without Markdown transformation

#### Scenario: Empty body

- **WHEN** a step body is empty
- **THEN** the step page renders no body block

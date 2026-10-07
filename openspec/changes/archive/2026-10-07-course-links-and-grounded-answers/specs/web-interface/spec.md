## MODIFIED Requirements

### Requirement: Formatted assistant answers

The assistant chat panel SHALL render assistant answers as Markdown: text wrapped in double
asterisks SHALL be shown in bold, a triple-backtick fenced code block SHALL be shown as a framed
code block preserving line breaks, inline code in single backticks SHALL be shown as framed inline
code, and a Markdown link `[text](target)` SHALL be shown as a clickable link. Only relative
targets that start with `/` and contain no scheme and no `//` SHALL be rendered as links; any other
target SHALL be shown as plain text. Text without Markdown SHALL be shown unchanged, preserving
line breaks. Answers SHALL be inserted as DOM nodes without interpreting raw HTML from the model.

#### Scenario: Bold text rendered
- **WHEN** an assistant answer contains `**важное**`
- **THEN** the panel shows «важное» in bold without the surrounding asterisks

#### Scenario: Fenced code block framed
- **WHEN** an assistant answer contains a fenced code block
- **THEN** the panel shows the code in a framed block with its line breaks preserved and without the fence markers

#### Scenario: Inline code framed
- **WHEN** an assistant answer contains inline code in backticks
- **THEN** the panel shows it as framed inline code without the backticks

#### Scenario: Course link rendered
- **WHEN** an assistant answer contains `[«Курс»](/courses/5)`
- **THEN** the panel shows «Курс» as a clickable link to `/courses/5` without the Markdown syntax

#### Scenario: Non-portal link shown as text
- **WHEN** an assistant answer contains a Markdown link whose target is not a relative platform path (for example `https://example.com`)
- **THEN** the panel shows the link text and target as plain text and does not create a link

#### Scenario: Plain answer preserved
- **WHEN** an assistant answer contains no Markdown
- **THEN** the panel shows the text unchanged, preserving line breaks

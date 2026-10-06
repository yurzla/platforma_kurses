## ADDED Requirements

### Requirement: Formatted assistant answers

The assistant chat panel SHALL render assistant answers as Markdown: text wrapped in double
asterisks SHALL be shown in bold, a triple-backtick fenced code block SHALL be shown as a framed
code block preserving line breaks, and inline code in single backticks SHALL be shown as framed
inline code. Text without Markdown SHALL be shown unchanged, preserving line breaks. Answers SHALL
be inserted as DOM nodes without interpreting raw HTML from the model.

#### Scenario: Bold text rendered
- **WHEN** an assistant answer contains `**важное**`
- **THEN** the panel shows «важное» in bold without the surrounding asterisks

#### Scenario: Fenced code block framed
- **WHEN** an assistant answer contains a fenced code block
- **THEN** the panel shows the code in a framed block with its line breaks preserved and without the fence markers

#### Scenario: Inline code framed
- **WHEN** an assistant answer contains inline code in backticks
- **THEN** the panel shows it as framed inline code without the backticks

#### Scenario: Plain answer preserved
- **WHEN** an assistant answer contains no Markdown
- **THEN** the panel shows the text unchanged, preserving line breaks

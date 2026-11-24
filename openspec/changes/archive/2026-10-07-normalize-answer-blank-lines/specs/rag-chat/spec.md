## MODIFIED Requirements

### Requirement: Markdown-formatted answers

The system SHALL instruct the language model to format assistant answers in Markdown, using bold
for emphasis, fenced code blocks for multi-line code (inline code for short fragments), and
Markdown links to platform courses in the form `[text](/courses/ID)`, so that the web panel can
render the formatting. The system SHALL also instruct the model to separate the answer's blocks
from each other with exactly one blank line, to separate list items from each other with exactly one
blank line, and to always place a blank line before the «Источники:» block. The system SHALL
additionally normalize the generated answer deterministically before persisting it, so that the
answer's blocks and adjacent list items are separated by exactly one blank line and a blank line
always precedes the «Источники:» block, without modifying fenced code blocks.

#### Scenario: Answer formatted in Markdown
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use Markdown bold and fenced code blocks

#### Scenario: Course reference uses a Markdown link
- **WHEN** the assistant refers to a platform course in its answer
- **THEN** the prompt instructs the model to use a Markdown link to that course page

#### Scenario: Blocks and list items separated by blank lines
- **WHEN** the assistant generates an answer with several blocks or list items
- **THEN** the prompt instructs the model to separate the blocks with exactly one blank line
- **AND** the prompt instructs the model to separate list items from each other with exactly one blank line
- **AND** the prompt instructs the model to place a blank line before the «Источники:» block

#### Scenario: Blank lines are normalized deterministically
- **WHEN** the assistant persists an answer in which list items or blocks are not separated by a blank line
- **THEN** the system inserts exactly one blank line between adjacent list items and between blocks
- **AND** the system places a blank line before the «Источники:» block
- **AND** the system leaves fenced code blocks unchanged

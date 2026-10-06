## ADDED Requirements

### Requirement: Markdown-formatted answers

The system SHALL instruct the language model to format assistant answers in Markdown, using bold
for emphasis and fenced code blocks for multi-line code (inline code for short fragments), so that
the web panel can render the formatting.

#### Scenario: Answer formatted in Markdown
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use Markdown bold and fenced code blocks

## Why

Answers and their list items are rendered too densely; blocks and list entries should be separated
by a blank line for readability.

## What Changes

- The Markdown-formatting instruction now also requires a blank line between the answer's blocks
  and between list items.
- Prompt-only change.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the markdown-formatted answers requirement now requires blank-line separation of
  blocks and list items.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 9).
- Tests: `tests/unit/test_domain.py`.

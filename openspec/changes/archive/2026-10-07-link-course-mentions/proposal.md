## Why

The model sometimes names a course in the answer body without any link (for example `**«Название»**`),
so the mention is not traceable and is inconsistent with the `Источники:` block, which does use links.
The prompt must require a Markdown link for every course mention anywhere in the answer.

## What Changes

- The answer prompt gains an explicit rule: every mention of a course — in the answer text, in a list,
  or in the `Источники:` block — MUST be a Markdown link `[«Название»](/courses/ID)`, with the title
  taken verbatim from the provided data; a course MUST NOT be mentioned without a link.
- Prompt-only change; sanitization, handlers, and the `allowed` course set are not modified.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the «Markdown-formatted answers» requirement now also requires a Markdown link for every
  mention of a course, not only for recommendations and the sources block.

## Impact

- Backend: `backend/src/courses_assistant/domain/prompts.py` (`SYSTEM_PROMPT`).
- Tests: `tests/unit/test_domain.py`.

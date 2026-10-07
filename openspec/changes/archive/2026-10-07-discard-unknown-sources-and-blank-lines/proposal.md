## Why

The «Источники:» block could contain a course/title that is not present in the provided data
(a model hallucination surviving as plain text after link stripping), and the blank-line formatting
rule was too soft to be followed. The sources exception must be reformulated so the block lists only
courses present in the provided data, and the blank-line rule must be hardened.

## What Changes

- The sources rule now requires including in «Источники:» only courses from the provided materials /
  recommended courses, discarding any course or title not present in the provided data; the block is
  omitted only when the provided data has no source course.
- The formatting rule is hardened: exactly one blank line between blocks, exactly one blank line
  between list items, and always a blank line before the «Источники:» block.
- Prompt-only changes; no code/sanitizer changes.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: reformulated the sources-block exception (only provided-data courses, discard others)
  and hardened the markdown blank-line requirement.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rules 7 and 9).
- Tests: `tests/unit/test_domain.py`.

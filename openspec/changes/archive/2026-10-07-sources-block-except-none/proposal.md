## Why

The «Источники:» block must be present in every answer; it may be omitted only when there are
genuinely no sources to cite. The previous exception was tied to a specific phrase; it should depend
on whether sources actually exist.

## What Changes

- The sources rule in the answer prompt now allows omitting the block only when there are really no
  sources to list.
- Prompt-only change; no code/sanitizer changes.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the grounded model-authored answer requirement now ties the only omission of the
  «Источники:» block to the absence of any sources.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 7).
- Tests: `tests/unit/test_domain.py`.

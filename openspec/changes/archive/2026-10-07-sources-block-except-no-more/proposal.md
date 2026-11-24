## Why

The «Источники:» block must be present in every answer, with a single exception: when the model
answers that no other suitable courses are left. The prompt must state this exception explicitly.

## What Changes

- The sources rule in the answer prompt now states the block is mandatory in every answer, except
  when the answer is exactly «Больше подходящих курсов в списке нет.».
- Prompt-only change; no code/sanitizer changes.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the grounded model-authored answer requirement now defines the only case in which the
  «Источники:» block may be omitted.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 7).
- Tests: `tests/unit/test_domain.py`.

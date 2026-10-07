## Why

The model sometimes labelled entries in the model-authored «Источники» block with the fragment
label (for example «Источник 1») instead of the course title, and the block format was not pinned.
The sources block must always be present and use the strict `Источники:` + bullet-link format.

## What Changes

- The answer prompt pins the sources block to the exact format: the label `Источники:` followed by
  bullet entries `- [«Title»](/courses/ID)`.
- The prompt forbids using a fragment label such as «Источник 1» as the link text; the real course
  title must be used.
- No behavior outside the prompt changes.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the grounded model-authored answer requirement now pins the sources block format and
  the link text (course title, not a fragment label).

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 7).
- Tests: `tests/unit/test_domain.py` (`test_system_prompt_requests_sources_block`).

## Why

The sources block must be a single comma-separated list of course links, not a bullet list, so the
rendered answer is compact.

## What Changes

- The answer prompt pins the sources block to a single line: `Источники: [«Title»](/courses/ID), [«Title 2»](/courses/ID)`.
- Everything else (mandatory block, real course titles, no fragment labels) is unchanged.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the grounded model-authored answer requirement now specifies a comma-separated,
  single-line sources list.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 7).
- Tests: `tests/unit/test_domain.py` (`test_system_prompt_requests_sources_block`).

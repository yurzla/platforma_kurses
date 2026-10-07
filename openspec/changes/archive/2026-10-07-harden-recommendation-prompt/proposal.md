## Why

When a student asked for «ещё курсы», the model padded the answer with courses outside the
provided «РЕКОМЕНДУЕМЫЕ КУРСЫ» section; those were then removed during sanitization, leaving an
empty list and a dangling «Источники:». The prompt must forbid recommending any course outside the
section and define what to answer when the section is exhausted.

## What Changes

- The recommendation rule in the answer prompt is hardened: recommend **only** courses from the
  «РЕКОМЕНДУЕМЫЕ КУРСЫ» section, never courses from history, lesson materials, or the model's own
  knowledge.
- When the student asks for «ещё»/other courses and the section has no more, the model MUST say
  that no other suitable courses are available instead of inventing new ones.
- Prompt-only change; `sanitize_course_recommendations` and the handlers are not modified.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: the grounded model-authored answer requirement now also defines the exhausted-list
  behavior (state that no other courses are available, never add courses outside the section).

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT` rule 6).
- Tests: `tests/unit/test_domain.py`.

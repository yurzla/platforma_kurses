## Why

The answer text and the «Источники» block were assembled by deterministic backend code, so the
persisted answer could contradict the model's own text and relied on the platform catalog being
injected into the prompt. The assistant must ground every answer strictly in the retrieved course
chunks, and the model itself must produce both the answer body and its sources list.

## What Changes

- **BREAKING** (behavior): the answer is produced by the LLM and grounded **only** in the provided
  course materials; the platform course catalog is no longer injected into the answer prompt.
- The model writes the «Источники» block itself; the backend no longer appends a deterministic
  sources section and no longer guarantees source completeness.
- The catalog-only answer branch (global chat with no retrieved chunks but a non-empty catalog) is
  removed; a global question without chunks returns the fixed "no material found" answer without
  calling the LLM.
- Course-recommendation questions are answered by the LLM from a «РЕКОМЕНДУЕМЫЕ КУРСЫ» prompt
  section built from the embedding matches; the recommender no longer returns a ready-made list.
- Retrieved material fragments are labelled `[Источник i]` again (was `[Материал i]`) so the model
  does not produce a duplicated sources heading.
- `recommendation_description_limit` is retained; `catalog_prompt_limit` is removed.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: answers grounded only in provided chunks; catalog removed from the prompt; the model
  authors the «Источники» block; catalog-only branch removed; fragments labelled `[Источник i]`.
- `course-recommendations`: the recommendation answer is composed by the LLM from the
  «РЕКОМЕНДУЕМЫЕ КУРСЫ» section instead of a deterministic list.

## Impact

- Backend: `domain/prompts.py` (`SYSTEM_PROMPT`, `build_answer_system_prompt`/`messages`),
  `domain/context.py` (`[Источник i]`), `domain/recommender.py`
  (`build_recommended_courses_section` replaces `render_recommendations`),
  `application/rag.py` (`generate_answer` drops `catalog`, adds `recommended_courses`),
  `application/handlers.py` (`process_question`), `config.py` (removes `catalog_prompt_limit`).
- Tests: `tests/unit/test_domain.py`, `tests/unit/test_handlers.py`,
  `tests/unit/test_recommender.py`, `tests/api/test_api.py`.
- Web: unchanged (links keep rendering as before).

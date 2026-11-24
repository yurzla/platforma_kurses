## 1. Prompt rule

- [x] 1.1 `domain/prompts.py`: add rule 10 to `SYSTEM_PROMPT` — every course mention (text, list,
  «Источники:») MUST be a Markdown link `[«Название»](/courses/ID)` with the verbatim title, and a
  course MUST NOT be mentioned without a link
- [x] 1.2 `tests/unit/test_domain.py`: add a test asserting the new rule text is present

## 2. Verification

- [x] 2.1 `make lint`, `make typecheck`, `make test-unit`
- [x] 2.2 `openspec validate link-course-mentions --strict`

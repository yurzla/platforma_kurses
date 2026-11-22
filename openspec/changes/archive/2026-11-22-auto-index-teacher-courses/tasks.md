## 1. Specification

- [x] Describe the asynchronous indexing behaviour and boundaries.

## 2. Implementation

- [x] Add index stream settings and a dedicated indexer entrypoint.
- [x] Implement idempotent indexing of a course description and repair chunk updates.
- [x] Enqueue after course creation and meaningful title/description changes.
- [x] Add the indexer to Compose.
- [x] Enqueue and incrementally index created or updated step materials.

## 3. Verification

- [x] Add focused unit tests for indexing and enqueue rules.
- [x] Compile changed Python modules and validate the Compose configuration.
- [ ] Run OpenSpec validation, lint, typecheck, and tests when their CLIs are available.

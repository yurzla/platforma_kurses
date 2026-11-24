## 1. Specification

- [x] 1.1 Описать требование «Pending answer indicator» в дельте `web-interface`.

## 2. Implementation

- [x] 2.1 Добавить `appendPending()` со спиннером и текстом в `web.js` и использовать её при
  отправке вопроса.
- [x] 2.2 Добавить стили `.chat-pending`, `.chat-spinner` и `@keyframes chat-spin` в `web.css`
  с вертикальным центрированием и reduced-motion.

## 3. Verification

- [x] 3.1 Проверки статики в `tests/web/test_web.py`.
- [x] 3.2 `node --check`, `make lint`, `make typecheck`, `make test`,
  `openspec validate assistant-pending-spinner --strict`.

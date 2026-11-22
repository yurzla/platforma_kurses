## 1. Specification

- [x] 1.1 Описать требование «Site footer» в дельте `web-interface`.

## 2. Implementation

- [x] 2.1 Добавить глобал `current_year` в `templating.py`.
- [x] 2.2 Добавить разметку футера в `base.html`.
- [x] 2.3 Добавить стили футера и прижатие к низу в `web.css`.
- [x] 2.4 Увеличить вертикальные отступы футера (высота больше, текст и логотип без изменений).
- [x] 2.5 Название и логотип футера по размеру как в header, иконка справа от названия.
- [x] 2.6 Отступ между названием и иконкой как в header (пробел + `margin-left: 2px`).

## 3. Verification

- [x] 3.1 Проверки футера на страницах входа и обучения в `tests/web/test_web.py`.
- [x] 3.2 `make lint`, `make typecheck`, `make test`, `openspec validate site-footer --strict`.

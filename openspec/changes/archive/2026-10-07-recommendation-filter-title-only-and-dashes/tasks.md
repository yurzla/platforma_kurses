## 1. Domain

- [x] 1.1 `_block_has_unknown_course`: проверять только первую строку пункта и её первую кавычечную фразу; сохранять пункт при валидной ссылке `/courses/ID`
- [x] 1.2 `_to_dash_lists` + `_NUM_ITEM_RE`: вне код-блоков `N.`/`N)` → `-` с сохранением отступа; подключить в `sanitize_course_recommendations`

## 2. Tests

- [x] 2.1 Регрессия: рекомендация с кавычечной фразой в описании сохраняется
- [x] 2.2 Обновить `test_removes_numbered_item_but_keeps_following` (пункт → `-`)
- [x] 2.3 Нумерованные списки (вкл. вложенные) → `-`; код-блок и числа в прозе не трогаются

## 3. Verification

- [x] 3.1 `make lint`, `make typecheck`, `make test` — зелёные
- [x] 3.2 Пересборка контейнеров и проверка запроса «курсы по фронтенд-разработке»
- [x] 3.3 `openspec validate recommendation-filter-title-only-and-dashes --strict` и архивация

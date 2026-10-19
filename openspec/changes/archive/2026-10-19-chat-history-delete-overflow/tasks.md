## 1. Fix

- [x] 1.1 `static/web.css`: `.history-item .history-session` — `flex: 1 1 0`, `min-width: 0`,
      `width: auto`

## 2. Verification

- [x] 2.1 Замер в headless Chrome: `scrollWidth == clientWidth` у `.history-item` и
      `.history-sessions`, правая граница корзины совпадает с правой границей строки
- [x] 2.2 `make lint`, `make typecheck`, `make test`
- [x] 2.3 `openspec validate chat-history-delete-overflow --strict`
- [x] 2.4 Пересобрать образ `web`, проверить историю в UI

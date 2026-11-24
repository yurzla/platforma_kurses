## 1. Web-разметка

- [x] 1.1 `templates/base.html`: перенести блок `#chat-actions` внутрь `#chat-log`
- [x] 1.2 `templates/_assistant_history.html`: заменить `×` на inline-SVG корзины, оставить
      `class="history-delete"`, `data-session-id`, `aria-label="Удалить диалог"`

## 2. Web-поведение

- [x] 2.1 `static/web.js`: после отрисовки сообщений и создания сессии переставлять `#chat-actions`
      в конец `#chat-log`
- [x] 2.2 `static/web.js`: сохранить скрытие блока в режиме истории и очистку ленты
- [x] 2.3 `static/web.css`: стили блока внизу диалога (прижат влево, компактные кнопки) и иконки
      корзины (красный hover)

## 3. Tests

- [x] 3.1 `tests/web`: кнопки выгрузки внутри `#chat-log`, у кнопки удаления есть `aria-label` и SVG
- [x] 3.2 `tests/web`: поведение прокси и экспорта не изменилось

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate chat-controls-placement --strict`
- [x] 4.3 Пересобрать образ `web`, проверить страницу курса и экспорт в UI

## 1. Markup and styles

- [x] 1.1 `templates/base.html`: модальный диалог `#confirm-modal` с подложкой, текстом и кнопками
- [x] 1.2 `static/web.css`: стили карточки, кнопки `.btn.danger`, `body.modal-open`

## 2. Behaviour

- [x] 2.1 `static/web.js`: `askConfirm`/`closeConfirm` на promise, закрытие по подложке и `Escape`
- [x] 2.2 заменить `window.confirm` в очистке истории и удалении одного диалога

## 3. Tests

- [x] 3.1 `tests/web`: на страницах с ассистентом есть `role="dialog"` и кнопки подтверждения

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate chat-history-confirm-modal --strict`
- [x] 4.3 Пересобрать `web`, проверить модалку в UI

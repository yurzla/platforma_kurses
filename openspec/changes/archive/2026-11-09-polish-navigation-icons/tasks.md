# Tasks

## 1. OpenSpec

- [x] 1.1 Добавить delta-спеку `web-interface`; проверить `openspec validate polish-navigation-icons --strict`

## 2. Иконки и шапка

- [x] 2.1 Положить Bootstrap Icons в `web/src/courses_web/static/vendor/bootstrap-icons/`
- [x] 2.2 Подключить CSS иконок в `base.html`
- [x] 2.3 Убрать «· обучение» и добавить иконку робота в `_topbar.html`
- [x] 2.4 Заменить надпись на кнопке ассистента иконкой с доступным именем

## 3. Кнопка поиска и подчёркивание

- [x] 3.1 Заменить текст «Найти» на иконку поиска
- [x] 3.2 Добавить `text-decoration: none` в `.btn`

## 4. Тесты и проверка

- [x] 4.1 Обновить web-тесты под иконки и отсутствие подчёркивания
- [x] 4.2 Прогнать `ruff`, `mypy`, `pytest` с integration env
- [x] 4.3 Пересобрать и перезапустить web-сервис
- [x] 4.4 Заархивировать изменение и запушить

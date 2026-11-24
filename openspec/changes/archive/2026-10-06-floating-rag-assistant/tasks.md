## 1. Разметка и контекст страниц

- [x] 1.1 В `web/src/courses_web/templates/base.html` под `{% if me and me.role and course_id %}` добавить FAB `#assistant-toggle` и drawer `#assistant-drawer` с `#chat-log`, `#chat-form`, `#chat-input`, `data-course-id="{{ course_id }}"`; проверить, что на дашборде, `/courses`, login/register виджет не рендерится
- [x] 1.2 Удалить инлайновую секцию `assistant-panel` из `web/src/courses_web/templates/step.html`, сохранив `window.STEP/COURSE_ID/ME`
- [x] 1.3 В `web/src/courses_web/routers/pages.py` передать `course_id` в контекст `course()`; проверить, что `course()` и `step()` рендерят `data-course-id`
- [x] 1.4 Удалить из виджета селектор курса (`#chat-course-row`, `#chat-course`) — контекст курса всегда известен

## 2. Клиентская логика и стили

- [x] 2.1 В `web/src/courses_web/static/web.js` вынести чат в generic-init по виджету, добавить open/close, использовать `data-course-id` напрямую (без выбора курса), убрать отправку `user_id`; проверить, что логика ответа на шаг не затронута
- [x] 2.2 В `web/src/courses_web/static/web.css` добавить стили `.assistant-fab` (fixed, bottom-left, z-index 60) и `.assistant-drawer` (fixed right, overlay, z-index 61, `.open`), растянуть `#chat-log`

## 3. Кэш статики

- [x] 3.1 Добавить `static_url()` (версия по mtime) в `templating.py` и использовать в `base.html`/`dashboard.html`; `/static/*` отдавать с `Cache-Control: no-cache`
- [x] 3.2 Проверки версионированных ссылок в `tests/web/test_web.py`

## 4. Тесты

- [x] 4.1 В `tests/web/test_web.py`: виджет есть на `/courses/10` и странице шага; отсутствует на `/courses`, `/dashboard`, `/login`; `make test-unit` проходит

## 5. Проверка

- [x] 5.1 `make lint`, `make typecheck`, `make test-unit` проходят без ошибок

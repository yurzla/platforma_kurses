## Why

Общий список `/courses` показывает все опубликованные курсы, и студенту негде быстро увидеть только те, которые он уже проходит. Нужна отдельная страница «Мои курсы» с начатыми курсами и их прогрессом.

## What Changes

- Новая страница `GET /my-courses` в web-сервисе: показывает только курсы, которые пользователь уже начал (есть запись enrollment), с прогрессом и числом шагов; для пустого списка — приглашение перейти в каталог.
- В верхнее меню добавляется вкладка «Мои курсы» для авторизованных пользователей.
- API каталога получает фильтр `GET /api/v1/courses?enrolled=true`, возвращающий только курсы с enrollment пользователя.
- Карточки курсов выносятся в общий шаблон и переиспользуются на `/courses` и `/my-courses`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-interface`: новая страница «Мои курсы» и вкладка навигации.
- `learning-catalog`: фильтрация списка курсов по признаку enrollment пользователя.

## Impact

- Backend: `application/ports.py`, `adapters/persistence/repositories.py`, `entrypoints/api/routers/catalog.py`.
- Web: `routers/pages.py`, `templates/_topbar.html`, `templates/_course_cards.html`, `templates/courses.html`, `templates/my_courses.html`.
- Тесты: `tests/fakes.py`, `tests/api/test_catalog.py`, `tests/web/test_web.py`.
- Схема БД и схема ответа `CourseSummaryRead` не меняются.

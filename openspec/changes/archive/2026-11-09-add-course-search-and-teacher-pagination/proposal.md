# Proposal

## Why

Студенческий каталог и «Мое обучение» растут, а найти нужный курс можно только
пролистывая страницы. Страница «Преподавание» показывает все курсы
преподавателя одним списком без поиска и пагинации. Нужны единообразные поиск
и постраничная выдача.

## What Changes

- `GET /api/v1/courses` получает параметр `search`: регистронезависимый поиск
  по названию и описанию, совместимый с `enrolled=true` и пагинацией.
- На `/courses` и `/my-courses` появляются форма поиска, сохранение запроса в
  пагинации и пустое состояние для отсутствующих совпадений.
- `GET /api/v1/teacher/courses` получает `search`, `limit`, `offset` и
  возвращает конверт `{items,total,limit,offset}`.
  **BREAKING**: раньше возвращался плоский массив.
- `/teacher` получает поиск и пагинацию по 10 курсов на страницу.
- Список курсов преподавателя переводится с прямого SQL на порт
  `CatalogRepository`, чтобы его можно было покрыть тестами через фейки.

## Capabilities

### New Capabilities

- `teacher-workspace`: список собственных курсов преподавателя с поиском,
  пагинацией и счётчиками.

### Modified Capabilities

- `learning-catalog`: добавляется поведение поиска в каталоге курсов.
- `web-interface`: добавляются поиск на списках курсов и пагинация/поиск на
  странице «Преподавание».

## Impact

- Backend: `domain/catalog.py`, `application/ports.py`,
  `adapters/persistence/repositories.py`, `entrypoints/api/routers/{catalog,teacher}.py`,
  `entrypoints/api/schemas.py`.
- Web: `routers/pages.py`, шаблоны `_list_search.html`, `_pagination.html`,
  `courses.html`, `my_courses.html`, `teacher_dashboard.html`, `web.css`.
- Тесты: `tests/api`, `tests/web`, `tests/fakes.py`.
- БД и миграции не меняются.

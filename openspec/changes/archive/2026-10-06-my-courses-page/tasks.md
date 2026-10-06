## 1. API-фильтр

- [x] 1.1 `application/ports.py`: `list_courses(user_id, *, enrolled_only: bool = False)`
- [x] 1.2 `adapters/persistence/repositories.py`: при `enrolled_only` фильтровать по наличию enrollment пользователя
- [x] 1.3 `entrypoints/api/routers/catalog.py`: query-параметр `enrolled: bool = False`
- [x] 1.4 `tests/fakes.py`: поддержать `enrolled_only`, считать прогресс/enrollment по курсу

## 2. Web-страница

- [x] 2.1 `routers/pages.py`: `GET /my-courses` (вызов `/api/v1/courses?enrolled=true`, редирект на логин)
- [x] 2.2 `templates/_course_cards.html`: общий вывод карточек + пустое состояние
- [x] 2.3 `templates/courses.html` и `templates/my_courses.html`: использовать общий шаблон
- [x] 2.4 `templates/_topbar.html`: вкладка «Мои курсы»

## 3. Тесты

- [x] 3.1 `tests/api/test_catalog.py`: фильтр `enrolled=true` и поведение без фильтра
- [x] 3.2 `tests/web/test_web.py`: страница показывает начатые курсы, скрывает неначатые, вкладка, пустое состояние, редирект анонима

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate my-courses-page --strict`
- [x] 4.2 Пересобрать и перезапустить `api` и `web`

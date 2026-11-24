## 1. UI

- [x] 1.1 `templates/_topbar.html`: вкладка «Мое обучение»
- [x] 1.2 `templates/my_courses.html`: `<title>` и `<h1>` «Мое обучение»

## 2. Тесты и спека

- [x] 2.1 `tests/web/test_web.py`: проверка новой подписи
- [x] 2.2 delta `web-interface`: MODIFIED «My courses page» с новым лейблом

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate rename-my-courses-label --strict`
- [x] 3.2 Пересборка `web`, e2e-проверка `?page`

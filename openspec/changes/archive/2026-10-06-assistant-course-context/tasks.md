## 1. Web

- [x] 1.1 `routers/pages.py`: передавать название курса на страницы курса и шага
- [x] 1.2 `templates/base.html`: пометка с названием курса в режиме `course`
- [x] 1.3 `static/web.css`: стиль `.assistant-course-note`
- [x] 1.4 `tests/web/test_web.py`: пометка на курсе/шаге

## 2. Проверка

- [x] 2.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate --all --strict`
- [x] 2.2 Пересборка `web`, проверка пометки на странице курса/шага и её отсутствия на списках

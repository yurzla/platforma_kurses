## 1. Step type

- [x] 1.1 `templates/step.html`: подписи типов, бейдж по `step.step_type`
- [x] 1.2 `templates/step.html`: условия формы ответа по `step.step_type`
- [x] 1.3 `tests/web`: бейдж для текстового и choice-шага, варианты ответа

## 2. Reached dots

- [x] 2.1 `routers/pages.py`: `reached` и `step` у каждой точки
- [x] 2.2 `templates/step.html`: класс `reached` и `data-step`
- [x] 2.3 `static/web.css`: синяя обводка достигнутых точек
- [x] 2.4 `static/web.js`: пересчёт `reached` после отметки шага
- [x] 2.5 `tests/web`: достигнутая точка этапа и модуля

## 3. Verification

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate step-type-badge-and-reached-dots --strict`
- [x] 3.3 Пересобрать `web`, проверить бейдж, варианты и обводку в UI

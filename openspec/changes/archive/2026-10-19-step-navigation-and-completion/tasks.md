## 1. Navigation

- [x] 1.1 `routers/pages.py`: плоский список шагов курса и соседи текущего шага
- [x] 1.2 `templates/step.html`: кнопки «← Назад» / «Вперёд →», `disabled` на краях
- [x] 1.3 `static/web.css`: стили `.step-nav` и неактивных кнопок

## 2. Completion state

- [x] 2.1 `templates/step.html`: при `step.completed` — зелёная неактивная «Выполнено»
- [x] 2.2 `static/web.js`: после успешной отметки — текст, класс `done`, `disabled`
- [x] 2.3 `static/web.css`: стиль `.btn.done`

## 3. Tests

- [x] 3.1 Web: ссылки на соседние шаги, `disabled` на первом/последнем, переход через уроки
- [x] 3.2 Web: выполненный шаг рендерит «Выполнено» и `disabled`

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate step-navigation-and-completion --strict`
- [x] 4.3 Пересобрать `web`, проверить навигацию и кнопку в UI

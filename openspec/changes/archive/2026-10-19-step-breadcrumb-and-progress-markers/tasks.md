## 1. Breadcrumbs

- [x] 1.1 `routers/pages.py`: `_step_context` (курс, модуль, этап, глобальный номер шага)
- [x] 1.2 `templates/step.html`: крошки с названиями и «Шаг N»

## 2. Progress bar

- [x] 2.1 `routers/pages.py`: `_step_markers` — модули крупными, этапы мелкими точками
- [x] 2.2 `templates/step.html`: точки `module`/`lesson` вместо штрихов
- [x] 2.3 `static/web.css`: убрать карточку, стили точек разного размера

## 3. Tests

- [x] 3.1 Web: крошки содержат курс, модуль, этап и «Шаг 2»
- [x] 3.2 Web: крупная точка модуля и мелкая точка этапа, совпадение границ даёт одну точку

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate step-breadcrumb-and-progress-markers --strict`
- [x] 4.3 Пересобрать `web`, проверить крошки и шкалу в UI

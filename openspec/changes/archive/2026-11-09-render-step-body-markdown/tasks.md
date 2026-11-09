# Tasks

## 1. OpenSpec

- [x] 1.1 Добавить delta-спеки `learning-catalog` и `web-interface`; проверить `openspec validate render-step-body-markdown --strict`

## 2. Рендеринг Markdown

- [x] 2.1 Добавить `markdown-it-py` в `web/pyproject.toml` и обновить `uv.lock`
- [x] 2.2 Реализовать `courses_web/markdown.py` и Jinja-фильтр `markdown`
- [x] 2.3 Перевести `step.html` на фильтр `markdown`

## 3. Подсказка

- [x] 3.1 Переписать подсказку в `_step_form.html` под Markdown

## 4. Тесты

- [x] 4.1 Юнит-тесты рендерера (Markdown, переносы, legacy HTML)
- [x] 4.2 Web-тесты страницы шага и подсказки

## 5. Проверка

- [x] 5.1 Прогнать `uv run ruff check .`, `uv run mypy`, `uv run pytest`
- [x] 5.2 Проверить `uv lock --check` и пересобрать web-образ
- [x] 5.3 Перезапустить web-сервис и заархивировать изменение

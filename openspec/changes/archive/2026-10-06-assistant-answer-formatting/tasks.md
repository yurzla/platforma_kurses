## 1. Web

- [x] 1.1 `static/assistant-format.js`: рендер `**жирный**`, инлайн-код и блоков кода (без innerHTML)
- [x] 1.2 `templates/base.html`: подключить `assistant-format.js` перед `web.js`
- [x] 1.3 `static/web.js`: использовать рендер для ответов ассистента (и в истории сообщений)
- [x] 1.4 `static/web.css`: стили `.chat-code` и `.chat-code-inline` (рамка)

## 2. Backend

- [x] 2.1 `domain/prompts.py`: правило оформлять ответ в Markdown

## 3. Тесты

- [x] 3.1 `tests/unit/test_domain.py`: промпт требует Markdown
- [x] 3.2 `tests/web/test_web.py`: страница подключает `assistant-format.js`

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate --all --strict`
- [x] 4.2 Пересборка `web`, `worker`; проверка рендера (жирный, блок кода)

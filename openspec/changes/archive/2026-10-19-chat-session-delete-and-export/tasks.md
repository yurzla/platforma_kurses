## 1. Backend API: удаление сессии

- [x] 1.1 `application/ports.py`: `ChatRepository.delete_session`, `JobRepository.delete_by_session`
- [x] 1.2 `adapters/persistence/repositories.py`: реализации через SQLAlchemy `delete()`
- [x] 1.3 `tests/fakes.py`: реализация в фейковых репозиториях (удаляет сессию, сообщения, jobs)
- [x] 1.4 `entrypoints/api/routers/chat.py`: `DELETE /api/v1/chat/sessions/{session_id}` → 204

## 2. Backend API: экспорт диалога

- [x] 2.1 `application/chat_export.py`: детерминированный Markdown-рендер диалога
- [x] 2.2 `fpdf2` в `backend/pyproject.toml`, `uv lock`; шрифт `DejaVuSans.ttf` в
      `adapters/export/fonts/` и чтение через `importlib.resources`
- [x] 2.3 `adapters/export/pdf.py`: PDF-рендер диалога (кириллица, переносы, страницы)
- [x] 2.4 `routers/chat.py`: `GET /api/v1/chat/sessions/{session_id}/export?format=md|pdf`
      (204 нет; 400 на неизвестный формат, `Content-Disposition: attachment`)

## 3. Web

- [x] 3.1 `templates/_assistant_history.html`: кнопка удаления диалога
- [x] 3.2 `templates/base.html`: контейнер кнопок «Скачать .md» / «Скачать .pdf»
- [x] 3.3 `static/web.js`: удаление с подтверждением, обновление истории, сброс открытого диалога
- [x] 3.4 `static/web.js`: показ/скрытие кнопок выгрузки и href на текущий `sessionId`
- [x] 3.5 `static/web.js`: нейтральный текст ошибки для `status=failed` и сетевых сбоев
- [x] 3.6 `static/web.css`: стили кнопок удаления и выгрузки

## 4. Tests

- [x] 4.1 `tests/api`: DELETE — 204 владельцу, 403 чужому, 404 неизвестной, 401 анониму; jobs удалены
- [x] 4.2 `tests/api`: экспорт — md/pdf 200 и заголовок, 400 на неизвестный формат, 403/401
- [x] 4.3 `tests/unit`: Markdown-рендер (порядок, роли, источники, курс)
- [x] 4.4 `tests/unit`: PDF начинается с `%PDF`, непустой, содержит текст
- [x] 4.5 `tests/web`: кнопки удаления/выгрузки в истории и диалоге, прокси DELETE

## 5. Verification

- [x] 5.1 `make lint`, `make typecheck`, `make test`
- [x] 5.2 Ручная проверка в UI: удаление диалога, скачивание .md/.pdf, нейтральная ошибка

## Why

Диалоги с ассистентом нельзя удалять: история копится, ошибочные и тестовые сессии остаются в
списке навсегда. При сбое генерации в панель выводится техническое описание ошибки из
`jobs.error` (`Ошибка: <текст исключения>`), которое ничего не говорит пользователю. Кроме того,
готовый диалог нельзя сохранить вне сервиса — например, передать преподавателю или приложить
к отчёту.

## What Changes

- `DELETE /api/v1/chat/sessions/{session_id}` — владелец или администратор удаляет чат-сессию
  вместе с её сообщениями и связанными job'ами; ответ `204`, ошибки `401/403/404` по аналогии с
  чтением истории.
- В истории ассистента у каждого диалога появляется кнопка удаления с подтверждением; если удалён
  открытый диалог, панель возвращается к списку истории.
- `GET /api/v1/chat/sessions/{session_id}/export?format=md|pdf` — выгрузка диалога файлом
  (`Content-Disposition: attachment`) в Markdown или PDF; доступ — владелец или администратор,
  неподдерживаемый формат — `400`.
- В панели ассистента при открытом диалоге появляются кнопки «Скачать .md» и «Скачать .pdf».
- При неудачной обработке вопроса панель показывает нейтральный текст
  «Произошла ошибка, попробуйте чуть позже.» вместо технического описания из `jobs.error`;
  техническое описание остаётся в БД, dead-letter stream и логах для операторов.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `rag-chat`: удаление чат-сессии и экспорт диалога в Markdown/PDF.
- `web-interface`: удаление диалога из истории, кнопки выгрузки, нейтральное сообщение об ошибке.
- `question-jobs`: техническое описание сбоя job'а остаётся внутренним и не выводится пользователю.

## Impact

- Backend API: `entrypoints/api/routers/chat.py` (DELETE и export), `entrypoints/api/schemas.py`
  (при необходимости).
- Backend application: `application/ports.py` (`ChatRepository.delete_session`,
  `JobRepository.delete_by_session`), новый модуль форматирования диалога.
- Backend adapters: `adapters/persistence/repositories.py`, новый адаптер PDF-выгрузки
  (fpdf2 + встроенный шрифт DejaVuSans для кириллицы).
- Web: `templates/_assistant_history.html`, `templates/base.html`, `static/web.js`, `static/web.css`.
- Зависимости: `fpdf2` в `backend/pyproject.toml`, обновление `uv.lock`.
- Тесты: `tests/api`, `tests/web`, `tests/unit`, обновление `tests/fakes.py`.
- Схема БД не меняется: `chat_messages` уже удаляются каскадом, job'ы сессии удаляются явно.

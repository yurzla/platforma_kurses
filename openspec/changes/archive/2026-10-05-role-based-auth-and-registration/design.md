## Context

Админ-доступ сейчас определяется env-креды (`ADMIN_USERNAME`/`ADMIN_PASSWORD`), а студенты входят отдельным эндпоинтом. Нужна единая модель: пользователь из таблицы `users`, права по роли, самостоятельная регистрация student/teacher, админ — только через CLI.

## Decisions

- **Единая сессия**: один ключ сессии `user` (id). `require_user` — любой вошедший; `require_admin` — роль `admin`, читается из БД на каждом запросе (смена роли применяется сразу). Оба — async-зависимости.
- **Роли**: значения из БД-constraint `student|teacher|admin`. Самостоятельная регистрация допускает только `student`/`teacher`; `admin` — только `create_user.py --role admin`. Админ-страница может выдать любую из трёх ролей.
- **Запрет смены своей роли**: админ не может менять роль самому себе (защита от локаута) → HTTP 403.
- **Пароли**: без изменений — scrypt (`domain/security.py`).
- **Env**: удалить `ADMIN_USERNAME`/`ADMIN_PASSWORD`; переименовать `ADMIN_SESSION_SECRET`/`ADMIN_COOKIE_SECURE`/`ADMIN_SESSION_MAX_AGE` → `SESSION_SECRET`/`COOKIE_SECURE`/`SESSION_MAX_AGE`. Пустой `SESSION_SECRET` → случайный на процесс + warning.
- **Схема БД**: без миграций — `users_role_check` и `idx_users_role` уже существуют.
- **Capability**: `student-auth` заменяется на `user-auth` (REMOVED + ADDED).

## Risks / Trade-offs

- Публичная регистрация с ролью `teacher` — доверие на слово (инвайтов нет по требованию).
- Эфемерный `SESSION_SECRET` при отсутствии env: сессии не переживут рестарт и не разделяются между процессами — приемлемо для dev, в прод задавать `SESSION_SECRET`.
- Rename capability в OpenSpec: дельта `student-auth` помечает требования REMOVED, `user-auth` добавляет новые; при archive первый становится пустым.

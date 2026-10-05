## Why

Сейчас доступ в админку определяется переменными окружения `ADMIN_USERNAME`/`ADMIN_PASSWORD`, а не ролью пользователя, и на портале нет самостоятельной регистрации. Нужно: единая аутентификация по таблице `users`, определение прав по роли, регистрация студента/преподавателя на портале, создание администратора только через консольный скрипт и админ-страница управления ролями.

## What Changes

- Убрать авторизацию администратора по `ADMIN_USERNAME`/`ADMIN_PASSWORD`; все права определяются ролью из таблицы `users` (`student`/`teacher`/`admin`).
- Единый вход по email+password для всех ролей; одна сессия (ключ `user`).
- Регистрация на портале с ролью `student` или `teacher`; роль `admin` при регистрации недоступна.
- Администратор создаётся только консольным скриптом `create_user --role admin`.
- Админ-раздел «Админ панель»: список пользователей и выдача любой роли (`student`/`teacher`/`admin`); запрет менять собственную роль.
- Переименовать env `ADMIN_SESSION_SECRET`/`ADMIN_COOKIE_SECURE`/`ADMIN_SESSION_MAX_AGE` → `SESSION_SECRET`/`COOKIE_SECURE`/`SESSION_MAX_AGE`.
- Переименовать capability `student-auth` → `user-auth`.

## Capabilities

### New Capabilities
- `user-auth`: единая аутентификация по `users`, вход и выход, текущий пользователь, самостоятельная регистрация student/teacher, хеширование паролей.
- `user-management`: админ-просмотр пользователей и назначение ролей.

### Modified Capabilities
- `ops-dashboard`: доступ к админ-API и разделу «Админ панель» определяется ролью `admin`, а не env-кредами.
- `web-interface`: единая форма входа (email+password), страница регистрации, ссылка «Админ панель».
- `platform-health`: из конфигурации убраны админ-креды; session-настройки переименованы.
- `learning-catalog`: доступ к каталогу — для любого аутентифицированного пользователя (не только `student`).

## Impact

- Backend: `domain` (роли, ошибки), `application` (порты/команды/обработчики), `adapters` (`SqlUserRepository`), `entrypoints/api` (зависимости, auth, admin, schemas), `config`, `scripts/create_user`.
- Web: страницы `/login`, `/register`, «Админ панель», вкладка «Пользователи», JS/CSS.
- Инфра/доки: `.env.example`, `docker-compose.yml`, `README.md`, `AGENTS.md`.
- Схему БД менять не нужно: constraint `users_role_check` уже допускает `student|teacher|admin`.

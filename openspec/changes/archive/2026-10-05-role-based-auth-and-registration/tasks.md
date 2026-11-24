## 1. OpenSpec

- [x] 1.1 Изменение `role-based-auth-and-registration` создано и валидно (`validate --strict`).

## 2. Backend: домен и приложение

- [x] 2.1 `UserRole`/`SELF_REGISTER_ROLES` в `domain/models.py`; ошибки `EmailAlreadyExists`, `InvalidRole`.
- [x] 2.2 Порт `UserRepository`: `list`, `count`, `set_role`.
- [x] 2.3 Команды `RegisterUser`, `ChangeUserRole` и обработчики (валидация ролей, уникальность email, запрет смены своей роли).

## 3. Backend: адаптеры и API

- [x] 3.1 `SqlUserRepository`: `list`/`count`/`set_role`.
- [x] 3.2 `dependencies.py`: единый ключ `user`, `get_current_user`/`require_user`/`require_admin`.
- [x] 3.3 `routers/auth.py`: `register`, `login`, `logout`, `me`; удалить admin/student-эндпоинты.
- [x] 3.4 `routers/admin.py`: доступ по роли + `GET/PATCH /api/v1/admin/users`.
- [x] 3.5 `routers/catalog.py`, `routers/chat.py`: перейти на `require_user`/сессию.
- [x] 3.6 `schemas.py`: `RegisterRequest`/`LoginRequest`/user-схемы; убрать admin/student login-схемы.
- [x] 3.7 `config.py`/`app.py`: убрать admin-креды; session-настройки и resolved-секрет.
- [x] 3.8 `scripts/create_user.py`: валидация роли (единственный путь создания админа).

## 4. Web

- [x] 4.1 `/login` (единая форма) и `/register` (student/teacher); `/logout`.
- [x] 4.2 Шаблоны: `login.html`, `register.html`, `dashboard.html` («Админ панель», вкладка «Пользователи»), `_topbar.html`.
- [x] 4.3 `dashboard.js`: вкладка «Пользователи», загрузка/выдача ролей; `web.css`.

## 5. Инфра и доки

- [x] 5.1 `.env.example`, `docker-compose.yml`: убрать admin-креды, session-env.
- [x] 5.2 `README.md`, `AGENTS.md`: вход/регистрация, создание админа, env.

## 6. Тесты

- [x] 6.1 `fakes.py`: list/count/set_role, роли.
- [x] 6.2 `test_admin.py` (по роли), `test_user_auth.py` (вход/регистрация), `test_users_admin.py`.
- [x] 6.3 `test_web.py` (вход/регистрация/«Админ панель»), `test_config.py`.

## 7. Проверка и архив

- [x] 7.1 `ruff → mypy → pytest` (+ integration), сборка образов, compose-smoke.
- [x] 7.2 `openspec archive role-based-auth-and-registration -y`; `openspec validate --all --strict`.

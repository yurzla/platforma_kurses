# Tasks

## 1. OpenSpec

- [x] 1.1 Добавить delta-спеку `user-auth`; проверить `openspec validate encrypt-user-passwords --strict`

## 2. Шифрование и конфигурация

- [x] 2.1 Добавить `cryptography` в backend-зависимости и обновить `uv.lock`
- [x] 2.2 Реализовать `encrypt_password`, `verify_password`, `generate_password_key`
- [x] 2.3 Добавить `PASSWORD_KEY` в настройки `.env.example` и compose

## 3. Использование ключа

- [x] 3.1 Обновить регистрацию, вход, админские операции и `create_user`
- [x] 3.2 Добавить скрипт `reset_passwords` с записью `.secrets/passwords.txt`

## 4. Тесты и документация

- [x] 4.1 Обновить тестовые хелперы и unit-тесты шифрования
- [x] 4.2 Обновить README и `docs/DB_SCHEMA.md`

## 5. Выкат

- [x] 5.1 Прогнать `ruff`, `mypy`, `pytest` с integration env
- [x] 5.2 Сгенерировать ключ, выполнить сброс паролей на локальной БД
- [x] 5.3 Пересобрать и перезапустить API/web, проверить вход
- [x] 5.4 Заархивировать изменение, закоммитить и запушить

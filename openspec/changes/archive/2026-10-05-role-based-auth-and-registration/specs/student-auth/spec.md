## REMOVED Requirements

### Requirement: Student login
**Reason**: Заменено единым входом по email/паролю для всех ролей (capability `user-auth`).
**Migration**: Использовать `POST /api/v1/auth/login` (email, password).

### Requirement: Student session and current user
**Reason**: Заменено единой сессией и определением текущего пользователя по роли (capability `user-auth`).
**Migration**: Использовать `GET /api/v1/auth/me` и `POST /api/v1/auth/logout`.

### Requirement: Password hashing
**Reason**: Перенесено без изменений (capability `user-auth`).
**Migration**: Хеширование scrypt перенесено в `user-auth`.

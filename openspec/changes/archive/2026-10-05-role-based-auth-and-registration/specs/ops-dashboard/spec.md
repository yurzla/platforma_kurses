## REMOVED Requirements

### Requirement: Admin login (username/password)
**Reason**: Доступ определяется ролью `admin` из таблицы `users`, а не переменными окружения.
**Migration**: Администратор создаётся скриптом `create_user --role admin`; вход — единый `POST /api/v1/auth/login`.

## ADDED Requirements

### Requirement: Admin authorization by role
The system SHALL protect the admin API and the admin page so that they are accessible only to authenticated users whose role is `admin`.

#### Scenario: Admin access granted
- **WHEN** an authenticated user with role `admin` calls the admin API or requests the admin page
- **THEN** the system returns the requested data or page

#### Scenario: Non-admin access denied
- **WHEN** an authenticated user whose role is not `admin` calls the admin API
- **THEN** the system responds with HTTP 403

#### Scenario: Anonymous access denied
- **WHEN** an unauthenticated client calls the admin API
- **THEN** the system responds with HTTP 401

#### Scenario: Role change takes effect
- **WHEN** a user's role is changed to `admin` or away from it
- **THEN** subsequent admin requests are authorized according to the current role

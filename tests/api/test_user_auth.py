"""API-тесты аутентификации и регистрации пользователей."""

from __future__ import annotations

import httpx

from courses_assistant.domain.security import hash_password, verify_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def make_app(store: FakeStore):
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_login_any_role_and_me() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_user("t@example.com", "Учитель", hash_password("pw"), "teacher")
    store.add_user("a@example.com", "Админ", hash_password("pw"), "admin")
    ac = make_app(store)
    async with ac:
        for email, role in (
            ("s@example.com", "student"),
            ("t@example.com", "teacher"),
            ("a@example.com", "admin"),
        ):
            await ac.post("/api/v1/auth/logout")
            ok = await ac.post(
                "/api/v1/auth/login", json={"email": email, "password": "pw"}
            )
            assert ok.status_code == 200
            assert ok.json()["role"] == role
            me = await ac.get("/api/v1/auth/me")
            assert me.json()["email"] == email


async def test_invalid_login() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        bad = await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "no"}
        )
        assert bad.status_code == 401
        unknown = await ac.post(
            "/api/v1/auth/login", json={"email": "x@example.com", "password": "pw"}
        )
        assert unknown.status_code == 401
        assert (await ac.get("/api/v1/auth/me")).json()["role"] is None


async def test_register_student_and_teacher() -> None:
    store = FakeStore()
    ac = make_app(store)
    async with ac:
        student = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "name": "Новый",
                "password": "secret",
                "role": "student",
            },
        )
        assert student.status_code == 201
        assert student.json()["role"] == "student"
        me = await ac.get("/api/v1/auth/me")
        assert me.json()["email"] == "new@example.com"

        await ac.post("/api/v1/auth/logout")
        teacher = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "t@example.com",
                "name": "Препод",
                "password": "secret",
                "role": "teacher",
            },
        )
        assert teacher.status_code == 201
        assert teacher.json()["role"] == "teacher"


async def test_register_admin_role_rejected() -> None:
    store = FakeStore()
    ac = make_app(store)
    async with ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "name": "Хакер",
                "password": "secret",
                "role": "admin",
            },
        )
    assert response.status_code == 422
    assert store.user_profiles == {}


async def test_register_duplicate_email() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "s@example.com",
                "name": "Другой",
                "password": "secret",
                "role": "student",
            },
        )
    assert response.status_code == 409


def test_password_hash_roundtrip() -> None:
    encoded = hash_password("secret")
    assert verify_password("secret", encoded) is True
    assert verify_password("other", encoded) is False
    assert verify_password("secret", "garbage") is False


async def _refresh_with(ac: httpx.AsyncClient, token: str) -> httpx.Response:
    return await ac.post(
        "/api/v1/auth/refresh", headers={"cookie": f"refresh_token={token}"}
    )


async def test_refresh_rotates_and_old_token_rejected() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        login = await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        assert login.status_code == 200
        old_refresh = ac.cookies.get("refresh_token")
        assert old_refresh

        refreshed = await ac.post("/api/v1/auth/refresh")
        assert refreshed.status_code == 200
        new_refresh = ac.cookies.get("refresh_token")
        assert new_refresh and new_refresh != old_refresh

        reuse = await _refresh_with(ac, old_refresh)
        assert reuse.status_code == 401
        revoked = await _refresh_with(ac, new_refresh)
        assert revoked.status_code == 401


async def test_logout_revokes_refresh_token() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        refresh = ac.cookies.get("refresh_token")
        logout = await ac.post("/api/v1/auth/logout")
        assert logout.status_code == 200
        me = await ac.get("/api/v1/auth/me")
        assert me.json()["role"] is None
        reuse = await _refresh_with(ac, refresh)
        assert reuse.status_code == 401


async def test_access_token_via_bearer() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as login_ac:
        await login_ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        token = login_ac.cookies.get("access_token")
        assert token
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ok = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert ok.json()["role"] == "student"
        bad_token = "invalid.token.value"
        bad = await ac.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"}
        )
        assert bad.status_code == 401
        anon = await ac.get("/api/v1/auth/me")
        assert anon.json()["role"] is None

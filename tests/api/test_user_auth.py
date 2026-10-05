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

"""API-тесты аутентификации студентов."""

from __future__ import annotations

import httpx

from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def make_app(store: FakeStore):
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_student_login_and_me() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        bad = await ac.post(
            "/api/v1/auth/student/login", json={"email": "s@example.com", "password": "no"}
        )
        assert bad.status_code == 401

        ok = await ac.post(
            "/api/v1/auth/student/login", json={"email": "s@example.com", "password": "pw"}
        )
        assert ok.status_code == 200
        assert ok.json()["role"] == "student"

        me = await ac.get("/api/v1/auth/me")
        assert me.json()["email"] == "s@example.com"

        await ac.post("/api/v1/auth/student/logout")
        assert (await ac.get("/api/v1/auth/me")).json()["role"] is None


async def test_non_student_role_rejected() -> None:
    store = FakeStore()
    store.add_user("t@example.com", "Учитель", hash_password("pw"), "teacher")
    ac = make_app(store)
    async with ac:
        response = await ac.post(
            "/api/v1/auth/student/login", json={"email": "t@example.com", "password": "pw"}
        )
    assert response.status_code == 401


def test_password_hash_roundtrip() -> None:
    encoded = hash_password("secret")
    from courses_assistant.domain.security import verify_password

    assert verify_password("secret", encoded) is True
    assert verify_password("other", encoded) is False
    assert verify_password("secret", "garbage") is False

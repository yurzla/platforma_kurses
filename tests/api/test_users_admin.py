"""API-тесты управления пользователями (админ)."""

from __future__ import annotations

import httpx
import pytest

from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def make_app(store: FakeStore):
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def seed_users(store: FakeStore) -> None:
    store.add_user("admin@example.com", "Админ", hash_password("pw"), "admin")
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_user("t@example.com", "Учитель", hash_password("pw"), "teacher")


def user_id(store: FakeStore, email: str) -> int:
    return next(user.id for user in store.user_profiles.values() if user.email == email)


@pytest.fixture
def store() -> FakeStore:
    store = FakeStore()
    seed_users(store)
    return store


async def login_admin(ac: httpx.AsyncClient) -> None:
    response = await ac.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "pw"}
    )
    assert response.status_code == 200


async def test_users_list_and_search(store: FakeStore) -> None:
    ac = make_app(store)
    async with ac:
        await login_admin(ac)
        all_users = await ac.get("/api/v1/admin/users")
        assert all_users.status_code == 200
        assert all_users.json()["total"] == 3

        searched = await ac.get("/api/v1/admin/users", params={"search": "t@example.com"})
        assert searched.json()["total"] == 1
        assert searched.json()["items"][0]["role"] == "teacher"

        paged = await ac.get("/api/v1/admin/users", params={"limit": 2, "offset": 0})
        assert len(paged.json()["items"]) == 2
        assert paged.json()["total"] == 3


async def test_change_role_to_admin_and_back(store: FakeStore) -> None:
    ac = make_app(store)
    sid = user_id(store, "s@example.com")
    async with ac:
        await login_admin(ac)
        changed = await ac.patch(f"/api/v1/admin/users/{sid}", json={"role": "admin"})
        assert changed.status_code == 200
        assert changed.json()["role"] == "admin"

        back = await ac.patch(f"/api/v1/admin/users/{sid}", json={"role": "student"})
        assert back.json()["role"] == "student"


async def test_cannot_change_own_role(store: FakeStore) -> None:
    ac = make_app(store)
    admin_id = user_id(store, "admin@example.com")
    async with ac:
        await login_admin(ac)
        response = await ac.patch(
            f"/api/v1/admin/users/{admin_id}", json={"role": "student"}
        )
    assert response.status_code == 403


async def test_invalid_role_rejected(store: FakeStore) -> None:
    ac = make_app(store)
    sid = user_id(store, "s@example.com")
    async with ac:
        await login_admin(ac)
        response = await ac.patch(
            f"/api/v1/admin/users/{sid}", json={"role": "superuser"}
        )
    assert response.status_code == 422


async def test_unknown_user_returns_404(store: FakeStore) -> None:
    ac = make_app(store)
    async with ac:
        await login_admin(ac)
        response = await ac.patch("/api/v1/admin/users/999", json={"role": "teacher"})
    assert response.status_code == 404


async def test_non_admin_forbidden() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        await ac.post("/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"})
        assert (await ac.get("/api/v1/admin/users")).status_code == 403

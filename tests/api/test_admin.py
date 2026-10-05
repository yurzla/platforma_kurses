"""API-тесты админки, дашборд-данных и доступа по роли."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from courses_assistant.domain.models import JobStatus, QuestionJob
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def _seed_jobs(store: FakeStore) -> None:
    now = datetime.now(UTC)
    store.jobs["j-done"] = QuestionJob(
        id="j-done",
        session_id=1,
        question="что такое python?",
        status=JobStatus.DONE,
        answer="ответ",
        attempts=0,
        created_at=now - timedelta(minutes=5),
        updated_at=now - timedelta(minutes=5),
    )
    store.jobs["j-failed"] = QuestionJob(
        id="j-failed",
        session_id=2,
        question="что такое asyncio?",
        status=JobStatus.FAILED,
        error="boom",
        attempts=3,
        created_at=now,
        updated_at=now,
    )


def make_app(store: FakeStore):
    container, _, broker = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test"), broker


def seed_admin(store: FakeStore, email: str = "admin@example.com", password: str = "s3cret"):
    store.add_user(email, "Админ", hash_password(password), "admin")


async def login(ac: httpx.AsyncClient, email: str, password: str) -> httpx.Response:
    return await ac.post("/api/v1/auth/login", json={"email": email, "password": password})


async def test_overview_counts_and_streams() -> None:
    store = FakeStore()
    _seed_jobs(store)
    seed_admin(store)
    ac, broker = make_app(store)
    await broker.move_to_dead("rag.requests", "rag.dead", {"job_id": "x"}, "err")
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["status_counts"] == {"done": 1, "failed": 1}
    assert any(stat["stream"] == "rag.requests" for stat in body["streams"])


async def test_jobs_list_and_filters() -> None:
    store = FakeStore()
    _seed_jobs(store)
    seed_admin(store)
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        all_jobs = await ac.get("/api/v1/admin/jobs")
        assert all_jobs.status_code == 200
        assert all_jobs.json()["total"] == 2

        filtered = await ac.get("/api/v1/admin/jobs", params={"status": "failed"})
        assert filtered.json()["total"] == 1
        assert filtered.json()["items"][0]["id"] == "j-failed"

        searched = await ac.get("/api/v1/admin/jobs", params={"search": "asyncio"})
        assert searched.json()["total"] == 1

        bad = await ac.get("/api/v1/admin/jobs", params={"status": "nope"})
        assert bad.status_code == 400


async def test_dlq_lists_entries() -> None:
    store = FakeStore()
    seed_admin(store)
    ac, broker = make_app(store)
    await broker.move_to_dead(
        "rag.requests", "rag.dead", {"job_id": "j1", "session_id": 5}, "boom"
    )
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/dlq")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["job_id"] == "j1"
    assert entries[0]["error"] == "boom"
    assert entries[0]["source_stream"] == "rag.requests"


async def test_anonymous_denied() -> None:
    store = FakeStore()
    ac, _ = make_app(store)
    async with ac:
        assert (await ac.get("/api/v1/admin/overview")).status_code == 401
        me = await ac.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["role"] is None


async def test_non_admin_denied() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    ac, _ = make_app(store)
    async with ac:
        ok = await login(ac, "s@example.com", "pw")
        assert ok.status_code == 200
        assert (await ac.get("/api/v1/admin/overview")).status_code == 403


async def test_admin_access_by_role() -> None:
    store = FakeStore()
    seed_admin(store)
    ac, _ = make_app(store)
    async with ac:
        bad = await login(ac, "admin@example.com", "wrong")
        assert bad.status_code == 401

        ok = await login(ac, "admin@example.com", "s3cret")
        assert ok.status_code == 200
        assert ok.json()["role"] == "admin"

        assert (await ac.get("/api/v1/admin/overview")).status_code == 200


async def test_logout_clears_session() -> None:
    store = FakeStore()
    seed_admin(store)
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        assert (await ac.get("/api/v1/admin/overview")).status_code == 200

        logout = await ac.post("/api/v1/auth/logout")
        assert logout.status_code == 200
        assert (await ac.get("/api/v1/admin/overview")).status_code == 401

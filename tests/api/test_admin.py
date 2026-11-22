"""API-тесты админки, дашборд-данных и доступа по роли."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from courses_assistant.domain.models import JobStatus, QuestionJob
from courses_assistant.entrypoints.api.app import create_app
from courses_assistant.entrypoints.api.routers import admin as admin_router
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore, encrypt_test_password


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
    store.add_user(email, "Админ", encrypt_test_password(password), "admin")


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
    await broker.move_to_dead(
        "rag.index.requests", "rag.index.dead", {"course_id": 7}, "ollama down"
    )
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/dlq")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2
    by_stream = {entry["dead_stream"]: entry for entry in entries}
    assert by_stream["rag.dead"]["job_id"] == "j1"
    assert by_stream["rag.dead"]["error"] == "boom"
    assert by_stream["rag.dead"]["source_stream"] == "rag.requests"
    assert by_stream["rag.index.dead"]["course_id"] == 7
    assert by_stream["rag.index.dead"]["source_stream"] == "rag.index.requests"


async def test_dlq_filtered_by_dead_stream() -> None:
    store = FakeStore()
    seed_admin(store)
    ac, broker = make_app(store)
    await broker.move_to_dead("rag.requests", "rag.dead", {"job_id": "j1"}, "boom")
    await broker.move_to_dead(
        "rag.index.requests", "rag.index.dead", {"course_id": 7}, "ollama down"
    )
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/dlq", params={"stream": "rag.index.dead"})
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["dead_stream"] == "rag.index.dead"
    assert entries[0]["course_id"] == 7


async def test_streams_include_kind_and_detail() -> None:
    store = FakeStore()
    seed_admin(store)
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/streams")
    assert response.status_code == 200
    streams = response.json()
    by_stream = {stream["stream"]: stream for stream in streams}
    assert by_stream["rag.index.requests"]["kind"] == "processing"
    assert by_stream["rag.index.dead"]["kind"] == "dead"
    assert by_stream["rag.index.requests"]["consumer_details"] == [
        {"name": "fake-1", "pending": 0, "idle": 0}
    ]


async def test_health_reports_workers(monkeypatch) -> None:
    store = FakeStore()
    seed_admin(store)

    async def fake_check(base_url: str, model: str, timeout: float = 3.0) -> tuple[bool, None]:
        return True, None

    monkeypatch.setattr(admin_router, "check_ollama_model", fake_check)
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/health")
    assert response.status_code == 200
    workers = {worker["name"]: worker for worker in response.json()["workers"]}
    assert set(workers) == {"chat", "indexer", "cron"}
    assert all(worker["available"] for worker in workers.values())


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
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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


DIAGNOSTIC_ROUTES = [
    "/api/v1/admin/chunks",
    "/api/v1/admin/chunks/1",
    "/api/v1/admin/index",
    "/api/v1/admin/health",
]


async def test_diagnostics_anonymous_denied() -> None:
    store = FakeStore()
    ac, _ = make_app(store)
    async with ac:
        for route in DIAGNOSTIC_ROUTES:
            assert (await ac.get(route)).status_code == 401


async def test_diagnostics_non_admin_denied() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "s@example.com", "pw")
        for route in DIAGNOSTIC_ROUTES:
            assert (await ac.get(route)).status_code == 403


async def test_admin_health_reports_dependencies(monkeypatch) -> None:
    store = FakeStore()
    seed_admin(store)

    async def fake_check(base_url: str, model: str, timeout: float = 3.0) -> tuple[bool, None]:
        return True, None

    monkeypatch.setattr(admin_router, "check_ollama_model", fake_check)
    ac, _ = make_app(store)
    async with ac:
        await login(ac, "admin@example.com", "s3cret")
        response = await ac.get("/api/v1/admin/health")
    assert response.status_code == 200
    body = response.json()
    assert body["dependencies"]["redis"] == "ok"
    assert body["dependencies"]["ollama"] == "ok"
    assert body["dependencies"]["postgres"] == "unavailable"
    assert body["status"] == "degraded"
    assert body["ollama_model_available"] is True
    assert body["jobs"] == {
        "last_done_at": None,
        "last_failed_at": None,
        "oldest_queued_at": None,
    }

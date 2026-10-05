"""API-тесты админки, дашборда и входа."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from courses_assistant.domain.models import JobStatus, QuestionJob
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


def make_app(store: FakeStore, username: str = "", password: str = ""):
    container, _, broker = build_test_container(store)
    container.settings.admin_username = username
    container.settings.admin_password = password
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test"), broker


async def test_overview_counts_and_streams() -> None:
    store = FakeStore()
    _seed_jobs(store)
    ac, broker = make_app(store)
    await broker.move_to_dead("rag.requests", "rag.dead", {"job_id": "x"}, "err")
    async with ac:
        response = await ac.get("/api/v1/admin/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["status_counts"] == {"done": 1, "failed": 1}
    assert any(stat["stream"] == "rag.requests" for stat in body["streams"])


async def test_jobs_list_and_filters() -> None:
    store = FakeStore()
    _seed_jobs(store)
    ac, _ = make_app(store)
    async with ac:
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
    ac, broker = make_app(store)
    await broker.move_to_dead(
        "rag.requests", "rag.dead", {"job_id": "j1", "session_id": 5}, "boom"
    )
    async with ac:
        response = await ac.get("/api/v1/admin/dlq")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["job_id"] == "j1"
    assert entries[0]["error"] == "boom"
    assert entries[0]["source_stream"] == "rag.requests"


async def test_open_access_when_no_credentials() -> None:
    store = FakeStore()
    ac, _ = make_app(store)
    async with ac:
        assert (await ac.get("/api/v1/admin/overview")).status_code == 200
        assert (await ac.get("/dashboard")).status_code == 200
        # /login без включённой аутентификации ведёт на дашборд
        login = await ac.get("/login")
        assert login.status_code == 303
        assert login.headers["location"] == "/dashboard"


async def test_admin_requires_login_when_configured() -> None:
    store = FakeStore()
    ac, _ = make_app(store, username="admin", password="s3cret")
    async with ac:
        unauthorized = await ac.get("/api/v1/admin/overview")
        assert unauthorized.status_code == 401

        bad = await ac.post(
            "/login", data={"username": "admin", "password": "wrong", "next": "/dashboard"}
        )
        assert bad.status_code == 401

        ok = await ac.post(
            "/login", data={"username": "admin", "password": "s3cret", "next": "/dashboard"}
        )
        assert ok.status_code == 303

        authorized = await ac.get("/api/v1/admin/overview")
        assert authorized.status_code == 200


async def test_logout_clears_session() -> None:
    store = FakeStore()
    ac, _ = make_app(store, username="admin", password="s3cret")
    async with ac:
        await ac.post(
            "/login", data={"username": "admin", "password": "s3cret", "next": "/dashboard"}
        )
        assert (await ac.get("/api/v1/admin/overview")).status_code == 200

        logout = await ac.post("/logout")
        assert logout.status_code == 303
        assert (await ac.get("/api/v1/admin/overview")).status_code == 401


async def test_dashboard_redirects_to_login() -> None:
    store = FakeStore()
    ac, _ = make_app(store, username="admin", password="s3cret")
    async with ac:
        denied = await ac.get("/dashboard")
        assert denied.status_code == 307
        assert denied.headers["location"].startswith("/login?next=")

        await ac.post(
            "/login", data={"username": "admin", "password": "s3cret", "next": "/dashboard"}
        )
        allowed = await ac.get("/dashboard")
        assert allowed.status_code == 200
        assert "Jobs" in allowed.text
        assert "/static/dashboard.js" in allowed.text


async def test_dashboard_renders() -> None:
    store = FakeStore()
    ac, _ = make_app(store)
    async with ac:
        response = await ac.get("/dashboard")
    assert response.status_code == 200
    assert "Jobs" in response.text
    assert "/static/dashboard.js" in response.text


async def test_login_page_and_theme_assets() -> None:
    store = FakeStore()
    ac, _ = make_app(store, username="admin", password="s3cret")
    async with ac:
        page = await ac.get("/login")
        assert page.status_code == 200
        assert "Вход в админку" in page.text
        assert "data-theme-toggle" in page.text
        assert "/static/theme.js" in page.text
        assert "/static/dashboard.js" not in page.text

        assert (await ac.get("/static/theme.js")).status_code == 200
        assert (await ac.get("/static/dashboard.css")).status_code == 200

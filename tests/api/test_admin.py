"""API-тесты админки и дашборда."""

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


def make_app(store: FakeStore, admin_token: str = ""):
    container, _, broker = build_test_container(store)
    container.settings.admin_token = admin_token
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


async def test_admin_requires_token_when_configured() -> None:
    store = FakeStore()
    token = "s3cret"
    ac, _ = make_app(store, admin_token=token)
    async with ac:
        unauthorized = await ac.get("/api/v1/admin/overview")
        assert unauthorized.status_code == 401

        authorized = await ac.get(
            "/api/v1/admin/overview", headers={"Authorization": f"Bearer {token}"}
        )
        assert authorized.status_code == 200

        via_query = await ac.get("/api/v1/admin/overview", params={"token": token})
        assert via_query.status_code == 200


async def test_dashboard_renders() -> None:
    store = FakeStore()
    ac, _ = make_app(store)
    async with ac:
        response = await ac.get("/dashboard")
    assert response.status_code == 200
    assert "Jobs" in response.text
    assert "/static/dashboard.js" in response.text


async def test_dashboard_requires_token_when_configured() -> None:
    store = FakeStore()
    ac, _ = make_app(store, admin_token="s3cret")
    async with ac:
        denied = await ac.get("/dashboard")
        assert denied.status_code == 401

        allowed = await ac.get("/dashboard", params={"token": "s3cret"})
        assert allowed.status_code == 200
        assert "admin_token" in allowed.cookies

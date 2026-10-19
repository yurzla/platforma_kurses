"""Тесты удаления чат-сессии и выгрузки диалога."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest

from courses_assistant.domain.catalog import CourseDetail
from courses_assistant.domain.models import ChatMessage, ChatSession, QuestionJob, Role
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def _client(store: FakeStore) -> httpx.AsyncClient:
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _seed_session(store: FakeStore, user_id: int) -> None:
    store.add_course(CourseDetail(id=10, title="Python", sections=[]))
    started = datetime(2026, 10, 17, 12, 30, tzinfo=UTC)
    store.sessions[1] = ChatSession(
        id=1, user_id=user_id, course_id=10, started_at=started
    )
    store.messages[1] = [
        ChatMessage(
            session_id=1,
            role=Role.USER,
            content="Что такое список?",
            created_at=started,
        ),
        ChatMessage(
            session_id=1,
            role=Role.ASSISTANT,
            content="Список — упорядоченная коллекция.",
            created_at=started,
            sources=[
                {
                    "chunk_id": 5,
                    "course_title": "Python",
                    "course_url": "/courses/10",
                }
            ],
        ),
    ]
    store.jobs["job-1"] = QuestionJob(
        id="job-1", session_id=1, question="Что такое список?", created_at=started
    )
    store.jobs["job-2"] = QuestionJob(
        id="job-2", session_id=99, question="Другой диалог", created_at=started
    )


@pytest.fixture
async def student_client(store: FakeStore) -> AsyncIterator[httpx.AsyncClient]:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    _seed_session(store, user.id)
    async with _client(store) as ac:
        login = await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        assert login.status_code == 200
        yield ac


async def test_delete_own_session_removes_messages_and_jobs(store: FakeStore) -> None:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    _seed_session(store, user.id)
    async with _client(store) as ac:
        await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        response = await ac.delete("/api/v1/chat/sessions/1")
        gone = await ac.get("/api/v1/chat/sessions/1/messages")

    assert response.status_code == 204
    assert 1 not in store.sessions
    assert 1 not in store.messages
    assert "job-1" not in store.jobs
    assert "job-2" in store.jobs
    assert gone.status_code == 404


async def test_delete_foreign_session_forbidden() -> None:
    store = FakeStore()
    owner = store.add_user("owner@example.com", "Owner", hash_password("pw"), "student")
    _seed_session(store, owner.id)
    async with _client(store) as other:
        await other.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "name": "Other",
                "password": "secret",
                "role": "student",
            },
        )
        response = await other.delete("/api/v1/chat/sessions/1")

    assert response.status_code == 403
    assert 1 in store.sessions


async def test_delete_unknown_session_returns_404() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    async with _client(store) as ac:
        await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        response = await ac.delete("/api/v1/chat/sessions/404")
    assert response.status_code == 404


async def test_delete_session_requires_auth() -> None:
    store = FakeStore()
    async with _client(store) as ac:
        response = await ac.delete("/api/v1/chat/sessions/1")
    assert response.status_code == 401


async def test_admin_can_delete_foreign_session() -> None:
    store = FakeStore()
    owner = store.add_user("owner@example.com", "Owner", hash_password("pw"), "student")
    store.add_user("admin@example.com", "Админ", hash_password("adminpw"), "admin")
    _seed_session(store, owner.id)
    async with _client(store) as admin:
        await admin.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "adminpw"},
        )
        response = await admin.delete("/api/v1/chat/sessions/1")

    assert response.status_code == 204
    assert 1 not in store.sessions


async def test_delete_all_sessions_removes_own_sessions_and_jobs(store: FakeStore) -> None:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    other = store.add_user("o@example.com", "Другой", hash_password("pw"), "student")
    _seed_session(store, user.id)
    started = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    store.sessions[2] = ChatSession(id=2, user_id=user.id, course_id=None, started_at=started)
    store.messages[2] = []
    store.jobs["job-3"] = QuestionJob(
        id="job-3", session_id=2, question="Без курса", created_at=started
    )
    store.sessions[3] = ChatSession(id=3, user_id=other.id, course_id=10, started_at=started)
    store.messages[3] = []
    async with _client(store) as ac:
        await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        response = await ac.delete("/api/v1/chat/sessions")

    assert response.status_code == 204
    assert 1 not in store.sessions
    assert 2 not in store.sessions
    assert 3 in store.sessions
    assert "job-1" not in store.jobs
    assert "job-3" not in store.jobs
    assert "job-2" in store.jobs


async def test_delete_all_sessions_can_be_scoped_to_course(store: FakeStore) -> None:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    _seed_session(store, user.id)
    started = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    store.sessions[2] = ChatSession(id=2, user_id=user.id, course_id=20, started_at=started)
    store.messages[2] = []
    store.sessions[3] = ChatSession(id=3, user_id=user.id, course_id=None, started_at=started)
    store.messages[3] = []
    async with _client(store) as ac:
        await ac.post(
            "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
        )
        response = await ac.delete("/api/v1/chat/sessions", params={"course_id": 10})

    assert response.status_code == 204
    assert 1 not in store.sessions
    assert 2 in store.sessions
    assert 3 in store.sessions
    assert "job-1" not in store.jobs


async def test_delete_all_sessions_requires_auth() -> None:
    store = FakeStore()
    async with _client(store) as ac:
        response = await ac.delete("/api/v1/chat/sessions")
    assert response.status_code == 401


async def test_export_markdown(student_client: httpx.AsyncClient) -> None:
    response = await student_client.get("/api/v1/chat/sessions/1/export?format=md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    disposition = response.headers["content-disposition"]
    assert disposition == 'attachment; filename="dialog-1-2026-10-17.md"'
    body = response.text
    assert "«Python»" in body
    assert "Вопрос" in body and "Ответ" in body
    assert "Что такое список?" in body
    assert "Список — упорядоченная коллекция." in body
    assert "Источники:" in body
    assert body.index("Что такое список?") < body.index("Список — упорядоченная коллекция.")


async def test_export_pdf(student_client: httpx.AsyncClient) -> None:
    response = await student_client.get("/api/v1/chat/sessions/1/export?format=pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="dialog-1-2026-10-17.pdf"'
    )
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


async def test_export_unknown_format_returns_400(student_client: httpx.AsyncClient) -> None:
    response = await student_client.get("/api/v1/chat/sessions/1/export?format=docx")
    assert response.status_code == 400


async def test_export_missing_format_returns_400(student_client: httpx.AsyncClient) -> None:
    response = await student_client.get("/api/v1/chat/sessions/1/export")
    assert response.status_code == 400


async def test_export_foreign_session_forbidden() -> None:
    store = FakeStore()
    owner = store.add_user("owner@example.com", "Owner", hash_password("pw"), "student")
    _seed_session(store, owner.id)
    async with _client(store) as other:
        await other.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "name": "Other",
                "password": "secret",
                "role": "student",
            },
        )
        response = await other.get("/api/v1/chat/sessions/1/export?format=md")
    assert response.status_code == 403


async def test_export_requires_auth() -> None:
    store = FakeStore()
    async with _client(store) as ac:
        response = await ac.get("/api/v1/chat/sessions/1/export?format=md")
    assert response.status_code == 401

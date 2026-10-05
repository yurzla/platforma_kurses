"""API-тесты через httpx ASGITransport и фейковый контейнер."""

from __future__ import annotations

import httpx
import pytest

from courses_assistant.adapters.tokens.jwt import JwtTokenService
from courses_assistant.application.commands import ProcessQuestion
from courses_assistant.application.handlers import Handlers
from courses_assistant.application.message_bus import MessageBus
from courses_assistant.config import Settings
from courses_assistant.container import Container
from courses_assistant.domain.models import RetrievedChunk
from courses_assistant.entrypoints.api.app import create_app
from tests.fakes import (
    FakeBroker,
    FakeEmbedder,
    FakeLLM,
    FakeStore,
    InMemoryUnitOfWork,
)


def build_test_container(store: FakeStore) -> tuple[Container, FakeStore, FakeBroker]:
    settings = Settings(gigachat_credentials="test")
    uow_factory = lambda: InMemoryUnitOfWork(store)  # noqa: E731
    llm = FakeLLM(default="ответ")
    embedder = FakeEmbedder()
    broker = FakeBroker()
    handlers = Handlers(
        uow_factory=uow_factory, llm=llm, embedder=embedder, broker=broker, settings=settings
    )
    bus = MessageBus()
    container = Container(
        settings=settings,
        engine=None,  # type: ignore[arg-type]
        session_factory=None,  # type: ignore[arg-type]
        uow_factory=uow_factory,
        llm=llm,
        embedder=embedder,
        broker=broker,
        tokens=JwtTokenService(
            secret="test-secret-key-for-jwt-tests-1234567890",
            algorithm="HS256",
            access_ttl=900,
        ),
        handlers=handlers,
        bus=bus,
    )
    return container, store, broker


@pytest.fixture
def client(store: FakeStore):
    store.courses.add(10)
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test"), container, store


async def _register(ac: httpx.AsyncClient) -> None:
    response = await ac.post(
        "/api/v1/auth/register",
        json={
            "email": "s@example.com",
            "name": "Студент",
            "password": "secret",
            "role": "student",
        },
    )
    assert response.status_code == 201


async def test_health() -> None:
    store = FakeStore()
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_full_ask_flow(client) -> None:
    ac, container, store = client
    async with ac:
        await _register(ac)

        created = await ac.post("/api/v1/chat/sessions", json={"course_id": 10})
        assert created.status_code == 201
        session_id = created.json()["id"]

        empty = await ac.get(f"/api/v1/chat/sessions/{session_id}/messages")
        assert empty.status_code == 200
        assert empty.json() == []

        accepted = await ac.post(
            f"/api/v1/chat/sessions/{session_id}/ask", json={"question": "что такое x?"}
        )
        assert accepted.status_code == 202
        job_id = accepted.json()["job_id"]

        queued = await ac.get(f"/api/v1/jobs/{job_id}")
        assert queued.status_code == 200
        assert queued.json()["status"] == "queued"

        store.chunks = [
            RetrievedChunk(
                chunk_id=1, text="материал", source_type="theory", lesson="L", distance=0.1
            )
        ]
        await container.handlers.process_question(
            ProcessQuestion(job_id=job_id, session_id=session_id, question="что такое x?")
        )

        done = await ac.get(f"/api/v1/jobs/{job_id}")
        assert done.status_code == 200
        body = done.json()
        assert body["status"] == "done"
        assert body["answer"] == "ответ"

        history = await ac.get(f"/api/v1/chat/sessions/{session_id}/messages")
        assert len(history.json()) == 2


async def test_chat_requires_auth(client) -> None:
    ac, _, _ = client
    async with ac:
        response = await ac.post("/api/v1/chat/sessions", json={"course_id": 10})
    assert response.status_code == 401


async def test_unknown_course_returns_404(client) -> None:
    ac, _, _ = client
    async with ac:
        await _register(ac)
        response = await ac.post("/api/v1/chat/sessions", json={"course_id": 999})
    assert response.status_code == 404


async def test_unknown_job_returns_404(client) -> None:
    ac, _, _ = client
    async with ac:
        await _register(ac)
        response = await ac.get("/api/v1/jobs/nope")
    assert response.status_code == 404


async def test_validation_error(client) -> None:
    ac, _, _ = client
    async with ac:
        await _register(ac)
        response = await ac.post("/api/v1/chat/sessions", json={"course_id": 0})
    assert response.status_code == 422


async def test_foreign_session_forbidden() -> None:
    store = FakeStore()
    store.courses.add(10)
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    async with (
        httpx.AsyncClient(transport=transport, base_url="http://test") as owner,
        httpx.AsyncClient(transport=transport, base_url="http://test") as other,
    ):
        await owner.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@example.com",
                "name": "Owner",
                "password": "secret",
                "role": "student",
            },
        )
        created = await owner.post("/api/v1/chat/sessions", json={"course_id": 10})
        session_id = created.json()["id"]

        await other.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "name": "Other",
                "password": "secret",
                "role": "student",
            },
        )
        forbidden = await other.get(f"/api/v1/chat/sessions/{session_id}/messages")
        assert forbidden.status_code == 403
        forbidden_ask = await other.post(
            f"/api/v1/chat/sessions/{session_id}/ask", json={"question": "привет"}
        )
        assert forbidden_ask.status_code == 403

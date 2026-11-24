"""Тесты web-слоя: кнопки удаления/выгрузки диалога и прокси этих запросов."""

from __future__ import annotations

from datetime import UTC, datetime

from courses_assistant.domain.models import ChatMessage, ChatSession, Role
from tests.fakes import FakeStore
from tests.web.test_web import build_stack, seed_student_and_course


def _seed_dialogue(store: FakeStore, session_id: int = 1) -> None:
    user = next(iter(store.user_profiles.values()))
    started = datetime(2026, 10, 17, 12, 30, tzinfo=UTC)
    store.sessions[session_id] = ChatSession(
        id=session_id, user_id=user.id, course_id=10, started_at=started
    )
    store.messages[session_id] = [
        ChatMessage(session_id=session_id, role=Role.USER, content="вопрос", created_at=started),
        ChatMessage(
            session_id=session_id, role=Role.ASSISTANT, content="ответ", created_at=started
        ),
    ]


async def test_history_has_delete_control(store: FakeStore) -> None:
    seed_student_and_course(store)
    _seed_dialogue(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses")
    assert page.status_code == 200
    assert 'class="history-delete"' in page.text
    assert 'id="history-clear"' in page.text
    assert 'data-session-id="1"' in page.text
    assert 'aria-label="Удалить диалог"' in page.text
    assert "<svg" in page.text


async def test_course_page_has_export_controls(store: FakeStore) -> None:
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses/10")
    assert page.status_code == 200
    assert 'id="chat-actions"' in page.text
    assert 'id="export-md"' in page.text
    assert 'id="export-pdf"' in page.text
    assert page.text.index('id="chat-log"') < page.text.index('id="chat-actions"')


async def test_assistant_has_confirm_modal(store: FakeStore) -> None:
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses")
    assert page.status_code == 200
    assert 'role="dialog"' in page.text
    assert 'id="confirm-modal"' in page.text
    assert 'id="confirm-cancel"' in page.text
    assert 'id="confirm-ok"' in page.text


async def test_proxy_deletes_session(store: FakeStore) -> None:
    seed_student_and_course(store)
    _seed_dialogue(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        response = await web.delete("/api/v1/chat/sessions/1")
        history = await web.get("/assistant/history")
    assert response.status_code == 204
    assert 1 not in store.sessions
    assert 'data-session-id="1"' not in history.text


async def test_proxy_clears_history(store: FakeStore) -> None:
    seed_student_and_course(store)
    _seed_dialogue(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        response = await web.delete("/api/v1/chat/sessions")
        history = await web.get("/assistant/history")
    assert response.status_code == 204
    assert not store.sessions
    assert "История пуста" in history.text
    assert 'id="history-clear"' not in history.text


async def test_proxy_downloads_markdown(store: FakeStore) -> None:
    seed_student_and_course(store)
    _seed_dialogue(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        response = await web.get("/api/v1/chat/sessions/1/export?format=md")
    assert response.status_code == 200
    assert response.headers["content-disposition"] == (
        'attachment; filename="dialog-1-2026-10-17.md"'
    )
    assert "вопрос" in response.text
    assert "ответ" in response.text

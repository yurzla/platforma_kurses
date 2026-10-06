"""Тесты обработчиков команд."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from courses_assistant.application.commands import (
    CreateChatSession,
    ProcessQuestion,
    RunCronTask,
    SendQuestion,
)
from courses_assistant.application.handlers import NO_MATERIALS_ANSWER, Handlers
from courses_assistant.config import Settings
from courses_assistant.domain.catalog import CourseDetail
from courses_assistant.domain.errors import SessionNotFound, UserNotFound
from courses_assistant.domain.models import JobStatus, RetrievedChunk, Role
from tests.fakes import FakeBroker, FakeEmbedder, FakeLLM, FakeStore, InMemoryUnitOfWork


def make_handlers(
    store: FakeStore,
    broker: FakeBroker,
    llm: FakeLLM,
    embedder: FakeEmbedder,
) -> Handlers:
    settings = Settings(gigachat_credentials="test")
    return Handlers(
        uow_factory=lambda: InMemoryUnitOfWork(store),
        llm=llm,
        embedder=embedder,
        broker=broker,
        settings=settings,
    )


@pytest.fixture
def handlers(store, broker, llm, embedder) -> Handlers:
    store.users.add(1)
    store.courses.add(10)
    return make_handlers(store, broker, llm, embedder)


async def test_create_session_unknown_user(store, broker, llm, embedder) -> None:
    handlers = make_handlers(store, broker, llm, embedder)
    with pytest.raises(UserNotFound):
        await handlers.create_session(CreateChatSession(user_id=999, course_id=10))


async def test_create_session_persists(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    assert session_id in store.sessions
    assert store.sessions[session_id].course_id == 10


async def test_create_session_without_course(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    assert store.sessions[session_id].course_id is None


async def test_process_question_global_uses_chunks(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = [
        RetrievedChunk(chunk_id=9, text="материал", source_type="theory", lesson="L", distance=0.3)
    ]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == "тестовый ответ"
    assert job.sources[0]["chunk_id"] == 9


async def test_process_question_global_uses_catalog_without_chunks(
    handlers, store, llm
) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.add_course(CourseDetail(id=10, title="Python", description="Основы", sections=[]))
    store.chunks = []
    job_id = await handlers.send_question(
        SendQuestion(session_id=session_id, question="какой курс посоветуешь?")
    )

    await handlers.process_question(
        ProcessQuestion(
            job_id=job_id, session_id=session_id, question="какой курс посоветуешь?"
        )
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == "тестовый ответ"
    assert "«Python»" in llm.calls[0][0].content


async def test_process_question_global_without_catalog_returns_no_materials(
    handlers, store
) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = []
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == NO_MATERIALS_ANSWER


async def test_send_question_unknown_session(handlers) -> None:
    with pytest.raises(SessionNotFound):
        await handlers.send_question(SendQuestion(session_id=123, question="?"))
    assert handlers._broker.published == []  # type: ignore[attr-defined]


async def test_send_question_enqueues(handlers, store, broker) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="что?"))

    job = store.jobs[job_id]
    assert job.status == JobStatus.QUEUED
    assert len(broker.published) == 1
    stream, payload = broker.published[0]
    assert stream == "rag.requests"
    assert payload["job_id"] == job_id


async def test_send_question_publish_failure_marks_failed(handlers, store, broker) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))

    async def boom(stream: str, payload: dict, maxlen: int | None = None) -> str:
        raise RuntimeError("redis down")

    broker.publish = boom  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        await handlers.send_question(SendQuestion(session_id=session_id, question="?"))

    jobs = list(store.jobs.values())
    assert jobs[-1].status == JobStatus.FAILED


async def test_process_question_with_materials(handlers, store, llm) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    store.chunks = [
        RetrievedChunk(chunk_id=7, text="материал", source_type="theory", lesson="L", distance=0.2)
    ]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == "тестовый ответ"
    assert job.sources[0]["chunk_id"] == 7

    messages = store.messages[session_id]
    assert [m.role for m in messages] == [Role.USER, Role.ASSISTANT]
    assert messages[1].used_chunk_ids == [7]


async def test_process_question_without_materials(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    store.chunks = []
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == NO_MATERIALS_ANSWER


async def test_process_question_is_idempotent(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )
    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    assert len(store.messages[session_id]) == 2


async def test_run_cron_task_purges_old_terminal_jobs(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    old_job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="?"))
    fresh_job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="??"))

    store.jobs[old_job_id].status = JobStatus.DONE
    store.jobs[old_job_id].updated_at = datetime.now(UTC) - timedelta(days=30)
    store.jobs[fresh_job_id].status = JobStatus.FAILED
    store.jobs[fresh_job_id].updated_at = datetime.now(UTC)

    await handlers.run_cron_task(
        RunCronTask(name="purge_terminal_jobs", payload={"older_than_days": 7})
    )

    assert old_job_id not in store.jobs
    assert fresh_job_id in store.jobs


async def test_run_cron_task_unknown_name_raises(handlers) -> None:
    with pytest.raises(ValueError):
        await handlers.run_cron_task(RunCronTask(name="nope", payload={}))

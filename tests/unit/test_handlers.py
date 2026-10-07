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
from courses_assistant.domain.recommender import CourseMatch
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


async def test_process_question_global_course_query_without_matches_returns_no_materials(
    handlers, store
) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = []
    question = "какой курс посоветуешь?"
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question=question))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == NO_MATERIALS_ANSWER


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
        RetrievedChunk(
            chunk_id=7,
            text="материал",
            source_type="theory",
            lesson="L",
            distance=0.2,
            course_id=10,
            course_title="Python",
        )
    ]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == "тестовый ответ"
    assert job.sources[0]["chunk_id"] == 7

    system_prompt = llm.calls[-1][0].content
    assert "ТЕКУЩИЙ КУРС СТУДЕНТА" in system_prompt
    assert "Не предлагай" in system_prompt
    assert "[«Python»](/courses/10)" in system_prompt

    messages = store.messages[session_id]
    assert [m.role for m in messages] == [Role.USER, Role.ASSISTANT]
    assert messages[1].used_chunk_ids == [7]


async def test_process_question_keeps_model_written_sources(
    store, broker, embedder
) -> None:
    llm = FakeLLM(
        default=(
            "Краткий ответ.\n\n"
            "Источники:\n- [«Python»](/courses/10)"
        )
    )
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    store.courses.add(10)
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    store.chunks = [
        RetrievedChunk(
            chunk_id=7,
            text="материал",
            source_type="theory",
            lesson="L",
            distance=0.2,
            course_id=10,
            course_title="Python",
        )
    ]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert "Источники:" in job.answer
    assert "[«Python»](/courses/10)" in job.answer


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
    assert "Источники:" not in job.answer


def _java_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=3,
        text="материал",
        source_type="theory",
        lesson="L",
        distance=0.1,
        course_id=7,
        course_title="Java",
    )


async def test_process_question_global_links_mentioned_source(store, broker, embedder) -> None:
    llm = FakeLLM(
        default="Советую курс [«Java»](/courses/7).\n\nИсточники:\n- [«Java»](/courses/7)"
    )
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = [_java_chunk()]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert "Источники:" in job.answer
    assert "[«Java»](/courses/7)" in job.answer
    assert job.sources[0]["course_id"] == 7
    assert job.sources[0]["course_url"] == "/courses/7"


async def test_process_question_global_returns_chunk_sources(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = [_java_chunk()]
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question="вопрос"))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="вопрос")
    )

    job = store.jobs[job_id]
    assert job.answer == "тестовый ответ"
    assert job.sources[0]["course_id"] == 7


async def test_process_question_removes_course_not_on_platform(store, broker, embedder) -> None:
    fake_title = "Практический мини-курс по JavaScript и Bootstrap 5"
    real_title = "Тесты и задачи по HTML, CSS и JavaScript"
    llm = FakeLLM(
        default=(
            "На платформе есть курсы:\n\n"
            f"1. **«{real_title}»**\n"
            "   - Тип: теория и практика\n\n"
            f"2. **«{fake_title}»**\n"
            "   - Описание: Bootstrap 5.\n\n"
            "Выбирайте курс."
        )
    )
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    store.add_course(CourseDetail(id=3, title=real_title, description="", sections=[]))
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    store.chunks = [
        RetrievedChunk(
            chunk_id=556,
            text="анонс курса",
            source_type="theory",
            lesson="L",
            distance=0.1,
            course_id=3,
            course_title=real_title,
        )
    ]
    job_id = await handlers.send_question(
        SendQuestion(session_id=session_id, question="курсы по js")
    )

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question="курсы по js")
    )

    job = store.jobs[job_id]
    assert fake_title not in job.answer
    assert "Bootstrap 5" not in job.answer
    assert real_title in job.answer


async def test_process_question_global_recommends_by_embeddings(store, broker, embedder) -> None:
    llm = FakeLLM(default="тестовый ответ")
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    store.recommendations = [
        CourseMatch(
            course_id=3,
            title="Тесты и задачи по HTML, CSS и JavaScript",
            description="Курс про JS",
            score=0.9,
        ),
        CourseMatch(
            course_id=10,
            title="Основы Frontend-разработки и веб-приложений",
            description="Frontend",
            score=0.88,
        ),
    ]
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    question = "какие курсы по js есть?"
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question=question))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
    )

    job = store.jobs[job_id]
    assert job.status == JobStatus.DONE
    assert job.answer == "тестовый ответ"
    assert job.sources == []
    assert len(llm.calls) == 2  # расширение запроса + ответ модели

    answer_prompt = llm.calls[-1][0].content
    assert "РЕКОМЕНДУЕМЫЕ КУРСЫ" in answer_prompt
    assert "[«Тесты и задачи по HTML, CSS и JavaScript»](/courses/3)" in answer_prompt
    assert "[«Основы Frontend-разработки и веб-приложений»](/courses/10)" in answer_prompt


async def test_process_question_separates_recommended_items_with_blank_lines(
    store, broker, embedder
) -> None:
    llm = FakeLLM(
        default=(
            "Да, вот дополнительные курсы:\n\n"
            "- [«Тесты и задачи по HTML, CSS и JavaScript»](/courses/3) — описание\n"
            "- [«Основы Frontend-разработки и веб-приложений»](/courses/10) — описание\n\n"
            "Источники: [«Тесты и задачи по HTML, CSS и JavaScript»](/courses/3), "
            "[«Основы Frontend-разработки и веб-приложений»](/courses/10)"
        )
    )
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    store.recommendations = [
        CourseMatch(
            course_id=3,
            title="Тесты и задачи по HTML, CSS и JavaScript",
            description="Курс про JS",
            score=0.9,
        ),
        CourseMatch(
            course_id=10,
            title="Основы Frontend-разработки и веб-приложений",
            description="Frontend",
            score=0.88,
        ),
    ]
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    question = "какие курсы по js есть?"
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question=question))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
    )

    answer = store.jobs[job_id].answer
    assert (
        "- [«Тесты и задачи по HTML, CSS и JavaScript»](/courses/3) — описание\n\n"
        "- [«Основы Frontend-разработки и веб-приложений»](/courses/10) — описание"
    ) in answer
    assert "\n\nИсточники:" in answer


async def test_process_question_puts_sources_block_on_its_own_line(store, broker, embedder) -> None:
    llm = FakeLLM(
        default=(
            "Вот рекомендации. "
            "Источники: [«Тесты и задачи по HTML, CSS и JavaScript»](/courses/3)"
        )
    )
    handlers = make_handlers(store, broker, llm, embedder)
    store.users.add(1)
    store.recommendations = [
        CourseMatch(
            course_id=3,
            title="Тесты и задачи по HTML, CSS и JavaScript",
            description="Курс про JS",
            score=0.9,
        ),
    ]
    session_id = await handlers.create_session(CreateChatSession(user_id=1))
    question = "какие курсы по js есть?"
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question=question))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
    )

    answer = store.jobs[job_id].answer
    assert "Вот рекомендации.\n\nИсточники:" in answer




async def test_process_question_course_session_ignores_recommender(handlers, store) -> None:
    session_id = await handlers.create_session(CreateChatSession(user_id=1, course_id=10))
    store.recommendations = [
        CourseMatch(course_id=3, title="JS", description="", score=0.9),
    ]
    store.chunks = [
        RetrievedChunk(
            chunk_id=7,
            text="материал",
            source_type="theory",
            lesson="L",
            distance=0.2,
            course_id=10,
            course_title="Python",
        )
    ]
    question = "курсы по js"
    job_id = await handlers.send_question(SendQuestion(session_id=session_id, question=question))

    await handlers.process_question(
        ProcessQuestion(job_id=job_id, session_id=session_id, question=question)
    )

    job = store.jobs[job_id]
    assert job.answer.startswith("тестовый ответ")
    assert "/courses/3" not in job.answer


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

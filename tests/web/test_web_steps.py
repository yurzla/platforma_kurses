"""Тесты страницы шага: навигация по соседям и состояние выполнения."""

from __future__ import annotations

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.domain.security import hash_password
from tests.fakes import FakeStore
from tests.web.test_web import build_stack


def _seed_course(store: FakeStore) -> int:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    lesson_one = LessonSummary(
        id=11,
        title="Урок 1",
        position=1,
        steps=[
            StepSummary(id=101, position=1, step_type="text"),
            StepSummary(id=102, position=2, step_type="text"),
        ],
    )
    lesson_two = LessonSummary(
        id=12,
        title="Урок 2",
        position=2,
        steps=[StepSummary(id=103, position=1, step_type="text")],
    )
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson_one, lesson_two])
    store.add_course(CourseDetail(id=10, title="Python", sections=[section]))
    return user.id


def _seed_two_sections(store: FakeStore) -> int:
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    first = SectionSummary(
        id=1,
        title="Модуль 1",
        position=1,
        lessons=[
            LessonSummary(
                id=11,
                title="Урок 1",
                position=1,
                steps=[
                    StepSummary(id=101, position=1, step_type="text"),
                    StepSummary(id=102, position=2, step_type="text"),
                ],
            )
        ],
    )
    second = SectionSummary(
        id=2,
        title="Модуль 2",
        position=2,
        lessons=[
            LessonSummary(
                id=12,
                title="Урок 2",
                position=1,
                steps=[StepSummary(id=103, position=1, step_type="text")],
            )
        ],
    )
    store.add_course(CourseDetail(id=10, title="Python", sections=[first, second]))
    return user.id


async def _open_step(store: FakeStore, step_id: int) -> str:
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get(f"/courses/10/steps/{step_id}")
    assert page.status_code == 200
    return page.text


async def test_step_links_to_previous_and_next(store: FakeStore) -> None:
    _seed_course(store)
    text = await _open_step(store, 102)
    assert 'href="/courses/10/steps/101">← Назад</a>' in text
    assert 'href="/courses/10/steps/103">Вперёд →</a>' in text


async def test_first_step_has_disabled_back_control(store: FakeStore) -> None:
    _seed_course(store)
    text = await _open_step(store, 101)
    assert '<button class="btn ghost" type="button" disabled>← Назад</button>' in text
    assert 'href="/courses/10/steps/102">Вперёд →</a>' in text


async def test_last_step_has_disabled_forward_control(store: FakeStore) -> None:
    _seed_course(store)
    text = await _open_step(store, 103)
    assert 'href="/courses/10/steps/102">← Назад</a>' in text
    assert '<button class="btn" type="button" disabled>Вперёд →</button>' in text


async def test_next_step_crosses_lesson_boundary(store: FakeStore) -> None:
    _seed_course(store)
    text = await _open_step(store, 102)
    assert 'href="/courses/10/steps/103">Вперёд →</a>' in text


async def test_completed_step_renders_done_button(store: FakeStore) -> None:
    user_id = _seed_course(store)
    store.progress[(user_id, 102)] = "passed"
    text = await _open_step(store, 102)
    assert "Выполнено</button>" in text
    assert 'class="btn done"' in text
    assert "Отметить выполненным" not in text
    assert 'disabled>Выполнено</button>' in text


async def test_step_shows_course_progress(store: FakeStore) -> None:
    user_id = _seed_two_sections(store)
    store.progress[(user_id, 101)] = "passed"
    text = await _open_step(store, 102)
    assert "Пройдено 1 из 3 шагов" in text
    assert "33.3%" in text
    assert 'aria-valuenow="33.3"' in text
    assert 'style="width: 33.3%"' in text


async def test_progress_bar_marks_module_boundaries(store: FakeStore) -> None:
    user_id = _seed_two_sections(store)
    store.progress[(user_id, 101)] = "passed"
    text = await _open_step(store, 102)
    assert text.count('class="step-progress-mark"') == 1
    assert 'style="left: 66.67%"' in text
    assert 'title="Модуль 1: 1 из 2 шагов"' in text


async def test_step_page_uses_refreshed_token_for_course_structure(store: FakeStore) -> None:
    _seed_two_sections(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        for cookie in web.cookies.jar:
            if cookie.name == "access_token":
                cookie.value = "broken-token"
        page = await web.get("/courses/10/steps/102")
    assert page.status_code == 200
    assert "Пройдено 0 из 3 шагов" in page.text
    assert 'href="/courses/10/steps/101"' in page.text
    assert 'href="/courses/10/steps/103"' in page.text

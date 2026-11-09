"""Тесты страницы шага: навигация по соседям и состояние выполнения."""

from __future__ import annotations

import re

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from tests.fakes import FakeStore, encrypt_test_password
from tests.web.test_web import build_stack


def _seed_course(store: FakeStore) -> int:
    user = store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
    user = store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    first = SectionSummary(
        id=1,
        title="Модуль 1",
        position=1,
        lessons=[
            LessonSummary(
                id=11,
                title="Урок 1",
                position=1,
                steps=[StepSummary(id=101, position=1, step_type="text")],
            ),
            LessonSummary(
                id=12,
                title="Урок 2",
                position=2,
                steps=[StepSummary(id=102, position=1, step_type="text")],
            ),
        ],
    )
    second = SectionSummary(
        id=2,
        title="Модуль 2",
        position=2,
        lessons=[
            LessonSummary(
                id=21,
                title="Урок 3",
                position=1,
                steps=[StepSummary(id=103, position=1, step_type="text")],
            )
        ],
    )
    store.add_course(CourseDetail(id=10, title="Python", sections=[first, second]))
    return user.id


def _seed_choice_course(store: FakeStore) -> int:
    user = store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    lesson = LessonSummary(
        id=11,
        title="Урок 1",
        position=1,
        steps=[StepSummary(id=101, position=1, step_type="choice")],
    )
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson])
    store.add_course(CourseDetail(id=10, title="Python", sections=[section]))
    store.answer_keys[101] = {
        "name": "choice",
        "options": {"is_multiple_choice": False},
        "choices": [
            {"id": 1, "text": "A", "is_correct": True},
            {"id": 2, "text": "B", "is_correct": False},
        ],
    }
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
    assert text.count('class="step-progress-dot module-dot"') == 1
    assert 'style="left: 66.67%"' in text
    assert 'title="Модуль 1"' in text


async def test_progress_bar_marks_lesson_boundaries(store: FakeStore) -> None:
    user_id = _seed_two_sections(store)
    store.progress[(user_id, 101)] = "passed"
    text = await _open_step(store, 102)
    assert text.count('class="step-progress-dot lesson-dot reached"') == 1
    assert 'style="left: 33.33%"' in text
    assert 'title="Урок 1"' in text


async def test_breadcrumbs_show_course_hierarchy_and_step_number(store: FakeStore) -> None:
    _seed_two_sections(store)
    text = await _open_step(store, 102)
    assert '<a href="/courses/10">Python</a>' in text
    assert "Модуль 1" in text
    assert "Урок 2" in text
    assert "Шаг 2" in text
    assert "шаг 2" not in text


async def test_step_type_badge_shows_label(store: FakeStore) -> None:
    _seed_course(store)
    text = await _open_step(store, 101)
    assert '<span class="step-type-badge">Текст</span>' in text


async def test_choice_step_shows_options_and_test_badge(store: FakeStore) -> None:
    _seed_choice_course(store)
    text = await _open_step(store, 101)
    assert '<span class="step-type-badge">Тест</span>' in text
    assert 'class="choice-option"' in text
    assert 'type="radio"' in text
    assert 'name="answer"' not in text


async def test_reached_markers_get_accent_outline(store: FakeStore) -> None:
    user_id = _seed_two_sections(store)
    store.progress[(user_id, 101)] = "passed"
    text = await _open_step(store, 102)
    assert 'class="step-progress-dot lesson-dot reached"' in text
    assert 'class="step-progress-dot module-dot reached"' not in text

    store.progress[(user_id, 102)] = "passed"
    text = await _open_step(store, 102)
    assert 'class="step-progress-dot lesson-dot reached"' in text
    assert 'class="step-progress-dot module-dot reached"' in text


async def test_progress_dots_are_white_with_grey_and_accent_outlines(store: FakeStore) -> None:
    web, api = build_stack(store)
    async with web, api:
        css = await web.get("/static/web.css")
    assert css.status_code == 200
    plain = re.search(r"\.step-progress-dot\.lesson-dot \{([^}]*)\}", css.text)
    assert plain is not None
    assert "background: #fff" in plain.group(1)
    assert "0 0 0 2px var(--border)" in plain.group(1)
    reached = re.search(r"\.step-progress-dot\.lesson-dot\.reached \{([^}]*)\}", css.text)
    assert reached is not None
    assert "0 0 0 2px var(--accent)" in reached.group(1)


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

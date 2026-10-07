"""Тесты фильтрации рекомендаций курсов."""

from __future__ import annotations

from courses_assistant.domain.recommendations import sanitize_course_recommendations

REAL_TITLE = "Тесты и задачи по HTML, CSS и JavaScript"
FAKE_TITLE = "Практический мини-курс по JavaScript и Bootstrap 5"

OBSERVED_ANSWER = f"""На нашей платформе есть несколько интересных курсов по JavaScript:

1. **«{REAL_TITLE}»**
   - Тип: теория и практика
   - Описание: Бесплатный курс.

2. **«{FAKE_TITLE}»**
   - Тип: теория и практика
   - Описание: В этом курсе вы будете изучать JavaScript и Bootstrap 5.

Выбирайте подходящий курс."""


def test_removes_list_item_with_unknown_course() -> None:
    result = sanitize_course_recommendations(OBSERVED_ANSWER, [(3, REAL_TITLE)])
    assert FAKE_TITLE not in result
    assert "Bootstrap 5" not in result
    assert REAL_TITLE in result


def test_keeps_allowed_recommendation() -> None:
    result = sanitize_course_recommendations(OBSERVED_ANSWER, [(3, REAL_TITLE)])
    assert f"- **«{REAL_TITLE}»**" in result
    assert "Бесплатный курс." in result


def test_strips_unknown_course_link() -> None:
    answer = "Смотрите [Курс](/courses/999)."
    assert sanitize_course_recommendations(answer, [(3, REAL_TITLE)]) == "Смотрите Курс."


def test_keeps_allowed_course_link() -> None:
    answer = "Смотрите [Курс](/courses/3)."
    assert sanitize_course_recommendations(answer, [(3, REAL_TITLE)]) == answer


def test_normalizes_course_link_with_inner_whitespace() -> None:
    answer = "Подробнее в курсе [«Python»]( /courses/1 )."
    result = sanitize_course_recommendations(answer, [(1, "Python")])
    assert result == "Подробнее в курсе [«Python»](/courses/1)."


def test_strips_unknown_course_link_with_inner_whitespace() -> None:
    answer = "Подробнее в курсе [«Python»]( /courses/999 )."
    result = sanitize_course_recommendations(answer, [(1, "Python")])
    assert result == "Подробнее в курсе «Python»."


def test_removes_numbered_item_but_keeps_following() -> None:
    answer = (
        f"1. **«{FAKE_TITLE}»**\n"
        f"2. **«{REAL_TITLE}»**\n"
    )
    result = sanitize_course_recommendations(answer, [(3, REAL_TITLE)])
    assert FAKE_TITLE not in result
    assert f"- **«{REAL_TITLE}»**" in result
    assert "2." not in result


def test_keeps_recommendation_with_quoted_phrase_in_description() -> None:
    description = "вы узнаете, как работает фронтенд «под капотом»"
    answer = (
        f"1. [«{REAL_TITLE}»](/courses/3) — {description}\n"
        f"2. [«{FAKE_TITLE}»](/courses/999) — другое\n"
    )
    result = sanitize_course_recommendations(answer, [(3, REAL_TITLE)])
    assert REAL_TITLE in result
    assert FAKE_TITLE not in result


def test_converts_numbered_lists_to_dashes() -> None:
    answer = (
        f"1. **«{REAL_TITLE}»**\n"
        f"   1. вложенный\n"
        f"2. второй\n"
        f"3) третий\n"
    )
    result = sanitize_course_recommendations(answer, [(3, REAL_TITLE)])
    assert result == (
        f"- **«{REAL_TITLE}»**\n"
        f"   - вложенный\n"
        f"- второй\n"
        f"- третий\n"
    )


def test_code_block_numbered_list_untouched() -> None:
    answer = f"```\n1. **«{FAKE_TITLE}»**\n```\n"
    result = sanitize_course_recommendations(answer, [(3, REAL_TITLE)])
    assert result == answer


def test_number_in_prose_not_converted() -> None:
    answer = "Версия 3.1 вышла в 2023. Году."
    assert sanitize_course_recommendations(answer, [(3, REAL_TITLE)]) == answer


def test_prose_mention_is_not_removed() -> None:
    answer = f"В материале урока упоминается «{FAKE_TITLE}»."
    assert sanitize_course_recommendations(answer, [(3, REAL_TITLE)]) == answer


def test_removes_recommendations_when_no_allowed_courses() -> None:
    result = sanitize_course_recommendations(OBSERVED_ANSWER, [])
    assert REAL_TITLE not in result
    assert FAKE_TITLE not in result


def test_drops_linked_item_with_unknown_title() -> None:
    answer = "1. [«Супер курс по языку JavaScript»](/courses/3)\n"
    result = sanitize_course_recommendations(answer, [(3, REAL_TITLE)])
    assert "Супер курс по языку JavaScript" not in result


def test_empty_answer_is_returned_as_is() -> None:
    assert sanitize_course_recommendations("", [(3, REAL_TITLE)]) == ""

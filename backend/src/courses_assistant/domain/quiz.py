"""Логика тестов: разбор ключей Stepik и автопроверка ответов."""

from __future__ import annotations

from typing import Any

AUTO_GRADED_TYPES = {"choice", "number", "string"}


def grading_mode(step_type: str) -> str:
    return "auto" if step_type in AUTO_GRADED_TYPES else "manual"


def _extract_choices(block: dict[str, Any]) -> list[Any]:
    containers: list[Any] = [block]
    for key in ("options", "source", "answer"):
        value = block.get(key)
        if isinstance(value, dict):
            containers.append(value)
    for container in containers:
        if isinstance(container, dict):
            choices = container.get("choices")
            if isinstance(choices, list) and choices:
                return choices
    return []


def _extract_scalar(block: dict[str, Any]) -> Any:
    containers: list[Any] = [block]
    for key in ("options", "answer", "source"):
        value = block.get(key)
        if isinstance(value, dict):
            containers.append(value)
    for container in containers:
        if isinstance(container, dict):
            for key in ("answer", "correct", "value"):
                if container.get(key) is not None:
                    return container[key]
    return None


def build_answer_key(step_type: str, block: dict[str, Any] | None) -> dict[str, Any] | None:
    """Извлекает ключ ответа из payload step-source. None, если ключа нет."""
    if not block:
        return None
    if step_type == "choice":
        raw_choices = _extract_choices(block)
        if not raw_choices:
            return None
        choices: list[dict[str, Any]] = []
        correct_ids: list[Any] = []
        for index, raw in enumerate(raw_choices):
            if isinstance(raw, dict):
                choice_id = raw.get("id", index)
                text = raw.get("text", "")
                is_correct = bool(raw.get("is_correct") or raw.get("correct"))
            else:
                choice_id = index
                text = str(raw)
                is_correct = False
            choices.append({"id": choice_id, "text": text})
            if is_correct:
                correct_ids.append(choice_id)
        options = block.get("options")
        is_multiple = (
            bool(options.get("is_multiple_choice")) if isinstance(options, dict) else False
        )
        return {
            "choices": choices,
            "correct_ids": correct_ids,
            "is_multiple_choice": is_multiple,
        }
    if step_type in ("number", "string"):
        value = _extract_scalar(block)
        return None if value is None else {"answer": value}
    return None


def correct_answer_for_display(
    step_type: str, key: dict[str, Any] | None
) -> Any | None:
    if key is None:
        return None
    if step_type == "choice":
        return key.get("correct_ids")
    if step_type in ("number", "string"):
        return key.get("answer")
    return None


def grade(step_type: str, key: dict[str, Any] | None, answer: Any) -> bool | None:
    """True/False при наличии ключа, None — если автопроверка невозможна."""
    if key is None:
        return None
    if step_type == "choice":
        correct = {str(item) for item in key.get("correct_ids", [])}
        if answer is None:
            given: set[str] = set()
        elif isinstance(answer, list):
            given = {str(item) for item in answer}
        else:
            given = {str(answer)}
        return given == correct
    if step_type == "number":
        try:
            return float(str(answer).strip()) == float(str(key.get("answer")).strip())
        except (TypeError, ValueError):
            return False
    if step_type == "string":
        return str(answer).strip() == str(key.get("answer")).strip()
    return None

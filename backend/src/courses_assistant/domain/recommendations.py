"""Детерминированная фильтрация рекомендаций курсов (чистые функции)."""

from __future__ import annotations

import re
from collections.abc import Sequence

_LINK_RE = re.compile(r"\[\s*([^\]]+?)\s*\]\s*\(\s*/courses/\s*(\d+)\s*\)")
_QUOTED_RE = re.compile(r"«([^»]+)»|\"([^\"]+)\"|“([^”]+)”")
_LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-*]|\d+[.)])\s+\S")
_NUM_ITEM_RE = re.compile(r"^(\s*)\d+[.)](\s+)")
_FENCE_RE = re.compile(r"^\s*```")


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _iter_quoted(text: str) -> list[str]:
    titles: list[str] = []
    for match in _QUOTED_RE.finditer(text):
        title = next(group for group in match.groups() if group is not None).strip()
        if title:
            titles.append(title)
    return titles


def _looks_like_course(title: str) -> bool:
    normalized = _normalize(title)
    return len(normalized) >= 5 and " " in normalized


def _is_known(title: str, allowed_titles: set[str]) -> bool:
    normalized = _normalize(title)
    if normalized in allowed_titles:
        return True
    return any(
        len(allowed) >= 5 and (normalized in allowed or allowed in normalized)
        for allowed in allowed_titles
    )


def _block_has_unknown_course(block: Sequence[str], allowed_titles: set[str]) -> bool:
    first_line = block[0]
    quoted = _iter_quoted(first_line)
    if not quoted:
        return False
    if any(_is_known(title, allowed_titles) for title in quoted):
        return False
    link_text = "\n".join(match.group(1) for match in _LINK_RE.finditer(first_line))
    linked_titles = [title for title in quoted if title in link_text]
    if linked_titles:
        return any(_looks_like_course(title) for title in linked_titles)
    title = quoted[0]
    return _looks_like_course(title)


def _strip_unknown_links(answer: str, allowed_ids: set[int]) -> str:
    def replace(match: re.Match[str]) -> str:
        title = match.group(1)
        course_id = int(match.group(2))
        if course_id in allowed_ids:
            return f"[{title}](/courses/{course_id})"
        return title

    return _LINK_RE.sub(replace, answer)


def _drop_unknown_recommendations(answer: str, allowed_titles: set[str]) -> str:
    lines = answer.split("\n")
    result: list[str] = []
    index = 0
    fence = False
    while index < len(lines):
        line = lines[index]
        if _FENCE_RE.match(line):
            fence = not fence
            result.append(line)
            index += 1
            continue
        item = None if fence else _LIST_ITEM_RE.match(line)
        if item is None:
            result.append(line)
            index += 1
            continue

        base = len(item.group(1))
        block = [line]
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if candidate.strip() == "":
                lookahead = cursor
                while lookahead < len(lines) and lines[lookahead].strip() == "":
                    lookahead += 1
                if lookahead < len(lines):
                    next_item = _LIST_ITEM_RE.match(lines[lookahead])
                    next_indent = len(lines[lookahead]) - len(lines[lookahead].lstrip())
                    if (next_item and len(next_item.group(1)) <= base) or (
                        not next_item and next_indent <= base
                    ):
                        break
                block.append(candidate)
                cursor += 1
                continue
            indent = len(candidate) - len(candidate.lstrip())
            next_item = _LIST_ITEM_RE.match(candidate)
            if next_item and indent <= base:
                break
            if indent > base:
                block.append(candidate)
                cursor += 1
                continue
            break

        if _block_has_unknown_course(block, allowed_titles):
            index = cursor
            while index < len(lines) and lines[index].strip() == "":
                index += 1
            continue
        result.extend(block)
        index = cursor

    return "\n".join(result)


def _to_dash_lists(answer: str) -> str:
    lines = answer.split("\n")
    result: list[str] = []
    fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            fence = not fence
            result.append(line)
            continue
        if not fence:
            line = _NUM_ITEM_RE.sub(r"\1-\2", line)
        result.append(line)
    return "\n".join(result)


def sanitize_course_recommendations(
    answer: str,
    allowed_courses: Sequence[tuple[int, str | None]],
) -> str:
    """Убирает из ответа рекомендации и ссылки на курсы, которых нет на платформе.

    ``allowed_courses`` — реальные курсы портала (id и название).
    """
    if not answer:
        return answer
    allowed_ids = {course_id for course_id, _ in allowed_courses}
    allowed_titles = {
        _normalize(title) for _, title in allowed_courses if title
    }
    sanitized = _strip_unknown_links(answer, allowed_ids)
    return _to_dash_lists(_drop_unknown_recommendations(sanitized, allowed_titles))

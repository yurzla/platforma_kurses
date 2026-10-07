"""Детерминированное форматирование ответа ассистента (чистые функции)."""

from __future__ import annotations

import re

_FENCE_RE = re.compile(r"^\s*```")
_LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-*]|\d+[.)])\s+\S")
_SOURCES_LABEL = "Источники:"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def is_list_item(line: str) -> bool:
    return _LIST_ITEM_RE.match(line) is not None


def _split_inline_sources_label(lines: list[str], sources_label: str) -> list[str]:
    result: list[str] = []
    fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            fence = not fence
            result.append(line)
            continue
        if not fence and not line.lstrip().startswith(sources_label):
            index = line.find(sources_label)
            if index != -1:
                head = line[:index].rstrip()
                tail = line[index:].strip()
                if head:
                    result.append(head)
                result.append(tail)
                continue
        result.append(line)
    return result


def _collapse_blank_runs(lines: list[str]) -> list[str]:
    result: list[str] = []
    fence = False
    blank_run = 0
    for line in lines:
        if _FENCE_RE.match(line):
            fence = not fence
            result.append(line)
            blank_run = 0
            continue
        if not fence and line.strip() == "":
            blank_run += 1
            if blank_run > 1:
                continue
            result.append(line)
            continue
        blank_run = 0
        result.append(line)
    return result


def _needs_blank_between(
    prev_kind: str | None,
    prev_indent: int,
    kind: str,
    indent: int,
    line: str,
    sources_label: str,
) -> bool:
    if prev_kind is None:
        return False
    if line.lstrip().startswith(sources_label):
        return True
    if kind == "item" and prev_kind == "item":
        return indent == prev_indent
    if kind == "text" and prev_kind == "item":
        return indent <= prev_indent
    if kind == "item" and prev_kind == "text":
        return True
    return False


def normalize_answer_spacing(
    answer: str,
    *,
    sources_label: str = _SOURCES_LABEL,
) -> str:
    """Приводит ответ к ровно одной пустой строке между блоками, пунктами и перед «Источники:».

    Блоки кода в тройных обратных кавычках не изменяются.
    """
    if not answer:
        return answer

    lines = answer.split("\n")
    lines = _split_inline_sources_label(lines, sources_label)
    lines = _collapse_blank_runs(lines)
    result: list[str] = []
    fence = False
    prev_kind: str | None = None
    prev_indent = 0
    prev_blank = False

    for line in lines:
        if _FENCE_RE.match(line):
            fence = not fence
            result.append(line)
            prev_kind, prev_indent, prev_blank = "text", _indent(line), False
            continue
        if fence:
            result.append(line)
            continue
        if line.strip() == "":
            result.append(line)
            prev_blank = True
            continue

        item = is_list_item(line)
        kind = "item" if item else "text"
        indent = _indent(line)
        if _needs_blank_between(prev_kind, prev_indent, kind, indent, line, sources_label):
            if not prev_blank:
                result.append("")
        result.append(line)
        prev_kind, prev_indent, prev_blank = kind, indent, False

    return "\n".join(result)

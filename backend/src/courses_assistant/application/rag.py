"""RAG use cases: rewrite вопроса и генерация ответа через LLM-порт."""

from __future__ import annotations

from collections.abc import Sequence

from courses_assistant.application.ports import LLM
from courses_assistant.domain.models import ChatMessage, LLMMessage, Role
from courses_assistant.domain.prompts import (
    build_answer_messages,
    build_rewrite_prompt,
)


async def rewrite_question(
    question: str,
    history: Sequence[ChatMessage],
    llm: LLM,
    temperature: float = 0.0,
) -> str:
    if not history:
        return question

    prompt = build_rewrite_prompt(question, history)
    messages = [LLMMessage(role=Role.USER, content=prompt)]
    rewritten = await llm.generate(messages, temperature=temperature)
    return rewritten.strip() or question


async def generate_answer(
    question: str,
    context: str,
    history: Sequence[ChatMessage],
    llm: LLM,
    temperature: float = 0.2,
    catalog: str = "",
) -> str:
    messages = build_answer_messages(
        question=question, context=context, history=history, catalog=catalog
    )
    return await llm.generate(messages, temperature=temperature)

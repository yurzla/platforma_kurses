"""Use-case подбора курсов: расширение запроса + эмбеддинг + отбор."""

from __future__ import annotations

from courses_assistant.application.ports import LLM, CourseRecommender, Embedder
from courses_assistant.domain.models import LLMMessage, Role
from courses_assistant.domain.prompts import build_recommendation_expansion_prompt
from courses_assistant.domain.recommender import CourseMatch, select_courses


async def rank_courses(
    question: str,
    *,
    llm: LLM,
    embedder: Embedder,
    recommender: CourseRecommender,
    model_name: str,
    top_k: int,
    margin: float,
    min_score: float,
    candidate_limit: int,
) -> list[CourseMatch]:
    """Ранжирует курсы платформы по семантической близости к запросу."""
    expansion = await llm.generate(
        [LLMMessage(role=Role.USER, content=build_recommendation_expansion_prompt(question))],
        temperature=0.0,
    )
    search_text = f"{question} {expansion}".strip()
    embedding = await embedder.embed(search_text)
    matches = await recommender.similar_courses(
        embedding, model_name=model_name, limit=candidate_limit
    )
    return select_courses(matches, top_k=top_k, margin=margin, min_score=min_score)

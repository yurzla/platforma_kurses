def build_context(chunks: list[dict]) -> str:
    parts = []

    for i, chunk in enumerate(chunks, start=1):
        lesson = chunk["lesson"] or "Без названия"
        part = (f"[Источник {i}]\nУрок: {lesson}\nТип: {chunk['source_type']}\n Материал:\n{chunk['text']}")
        parts.append(part)
    return "\n\n".join(parts)
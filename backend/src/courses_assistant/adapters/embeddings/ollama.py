"""Embeddings через Ollama (nomic-embed-text)."""

from __future__ import annotations

import httpx

from courses_assistant.application.ports import Embedder
from courses_assistant.domain.errors import ExternalServiceError


class OllamaEmbedder(Embedder):
    def __init__(
        self,
        url: str,
        model: str,
        dimension: int,
        timeout: float = 120.0,
    ) -> None:
        self._url = url
        self._model = model
        self._dimension = dimension
        self._timeout = timeout

    async def embed(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._url,
                    json={"model": self._model, "input": text},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Ollama недоступна: {exc}") from exc

        data = response.json()
        try:
            embedding = data["embeddings"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExternalServiceError("Некорректный ответ Ollama: нет embeddings") from exc

        if len(embedding) != self._dimension:
            raise ExternalServiceError(
                f"Ожидалась размерность {self._dimension}, получено {len(embedding)}"
            )
        return [float(value) for value in embedding]


def _tags_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api/embed"):
        base = base[: -len("/api/embed")]
    return base + "/api/tags"


async def check_ollama_model(
    base_url: str,
    model: str,
    timeout: float = 3.0,
) -> tuple[bool, str | None]:
    """Проверяет доступность Ollama и наличие модели без генерации эмбеддинга.

    Возвращает (доступна ли модель, текст ошибки или None). Сетевые ошибки не
    пробрасываются: для диагностики достаточно факта недоступности.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(_tags_url(base_url))
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return False, f"Ollama недоступна: {exc}"

    raw_models = data.get("models") if isinstance(data, dict) else None
    names = {
        str(item.get("name") or item.get("model") or "")
        for item in (raw_models or [])
        if isinstance(item, dict)
    }
    wanted = model.split(":", 1)[0]
    if any(name.split(":", 1)[0] == wanted for name in names if name):
        return True, None
    return False, f"Модель {model} не загружена"

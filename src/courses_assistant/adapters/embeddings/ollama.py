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

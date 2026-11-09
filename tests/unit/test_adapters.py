"""Тесты адаптеров LLM и embeddings через respx."""

from __future__ import annotations

import httpx
import pytest
import respx

from courses_assistant.adapters.embeddings.ollama import OllamaEmbedder, check_ollama_model
from courses_assistant.adapters.llm.gigachat import GigaChatLLM
from courses_assistant.domain.errors import ExternalServiceError
from courses_assistant.domain.models import LLMMessage, Role


async def test_ollama_embedder_success() -> None:
    embedder = OllamaEmbedder(
        url="http://ollama.local/api/embed", model="nomic-embed-text", dimension=3
    )
    with respx.mock:
        respx.post("http://ollama.local/api/embed").mock(
            return_value=httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})
        )
        embedding = await embedder.embed("привет")
    assert embedding == [0.1, 0.2, 0.3]


async def test_ollama_embedder_dimension_mismatch() -> None:
    embedder = OllamaEmbedder(
        url="http://ollama.local/api/embed", model="nomic-embed-text", dimension=768
    )
    with respx.mock:
        respx.post("http://ollama.local/api/embed").mock(
            return_value=httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})
        )
        with pytest.raises(ExternalServiceError):
            await embedder.embed("привет")


async def test_gigachat_generates_answer() -> None:
    llm = GigaChatLLM(
        credentials="creds",
        scope="GIGACHAT_API_PERS",
        auth_url="https://auth.local/oauth",
        base_url="https://giga.local/v1",
        model="GigaChat-2",
    )
    with respx.mock:
        respx.post("https://auth.local/oauth").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok", "expires_at": 9_999_999_999_000}
            )
        )
        respx.post("https://giga.local/v1/chat/completions").mock(
            return_value=httpx.Response(
                200, json={"choices": [{"message": {"content": "ответ"}}]}
            )
        )
        result = await llm.generate([LLMMessage(role=Role.USER, content="привет")], 0.2)
    assert result == "ответ"


async def test_gigachat_requires_credentials() -> None:
    llm = GigaChatLLM(
        credentials="",
        scope="GIGACHAT_API_PERS",
        auth_url="https://auth.local/oauth",
        base_url="https://giga.local/v1",
        model="GigaChat-2",
    )
    with pytest.raises(ExternalServiceError):
        await llm.generate([LLMMessage(role=Role.USER, content="привет")], 0.2)


async def test_check_ollama_model_available() -> None:
    with respx.mock:
        respx.get("http://ollama.local/api/tags").mock(
            return_value=httpx.Response(
                200, json={"models": [{"name": "nomic-embed-text:latest"}]}
            )
        )
        available, error = await check_ollama_model(
            "http://ollama.local/api/embed", "nomic-embed-text"
        )
    assert available is True
    assert error is None


async def test_check_ollama_model_missing() -> None:
    with respx.mock:
        respx.get("http://ollama.local/api/tags").mock(
            return_value=httpx.Response(200, json={"models": [{"name": "qwen2:7b"}]})
        )
        available, error = await check_ollama_model(
            "http://ollama.local/api/embed", "nomic-embed-text"
        )
    assert available is False
    assert error is not None
    assert "не загружена" in error


async def test_check_ollama_model_unreachable() -> None:
    with respx.mock:
        respx.get("http://ollama.local/api/tags").mock(
            side_effect=httpx.ConnectError("no connection")
        )
        available, error = await check_ollama_model(
            "http://ollama.local/api/embed", "nomic-embed-text"
        )
    assert available is False
    assert error is not None
    assert "недоступна" in error

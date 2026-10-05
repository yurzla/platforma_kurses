"""LLM через GigaChat REST API (httpx, OAuth token cache)."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Sequence

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from courses_assistant.application.ports import LLM
from courses_assistant.domain.errors import ExternalServiceError
from courses_assistant.domain.models import LLMMessage

_TOKEN_SAFETY_MARGIN_SECONDS = 30.0
_DEFAULT_TOKEN_TTL_SECONDS = 1800.0


class _RetryableStatus(Exception):
    pass


class GigaChatLLM(LLM):
    def __init__(
        self,
        credentials: str,
        scope: str,
        auth_url: str,
        base_url: str,
        model: str,
        verify_ssl: bool = False,
        timeout: float = 120.0,
    ) -> None:
        self._credentials = credentials
        self._scope = scope
        self._auth_url = auth_url
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def generate(self, messages: Sequence[LLMMessage], temperature: float) -> str:
        if not self._credentials:
            raise ExternalServiceError("Не задан GIGACHAT_CREDENTIALS.")
        payload = {
            "model": self._model,
            "messages": [{"role": str(m.role), "content": m.content} for m in messages],
            "temperature": temperature,
        }
        return await self._chat_with_retry(payload)

    @retry(
        retry=retry_if_exception_type(_RetryableStatus),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _chat_with_retry(self, payload: dict) -> str:
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=self._timeout, verify=self._verify_ssl) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            if response.status_code == 401:
                self._token = None
                token = await self._get_token()
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
            if response.status_code in (429, 500, 502, 503, 504, 529):
                raise _RetryableStatus(f"GigaChat status {response.status_code}")
            if response.status_code >= 400:
                raise ExternalServiceError(
                    f"GigaChat вернул {response.status_code}: {response.text[:300]}"
                )
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise ExternalServiceError(
                f"GigaChat вернул не-JSON ответ ({content_type}): {response.text[:200]}"
            )
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ExternalServiceError("Некорректный ответ GigaChat") from exc

    async def _get_token(self) -> str:
        async with self._lock:
            now = time.time()
            if self._token and now < self._expires_at - _TOKEN_SAFETY_MARGIN_SECONDS:
                return self._token
            return await self._fetch_token()

    async def _fetch_token(self) -> str:
        headers = {
            "Authorization": f"Basic {self._credentials}",
            "RqUID": str(uuid.uuid4()),
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, verify=self._verify_ssl
            ) as client:
                response = await client.post(
                    self._auth_url, headers=headers, data={"scope": self._scope}
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Не удалось получить токен GigaChat: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError(
                "GigaChat вернул не-JSON при получении токена"
            ) from exc
        token = data.get("access_token")
        if not token:
            raise ExternalServiceError("GigaChat не вернул access_token")
        expires_at = data.get("expires_at")
        if expires_at:
            self._expires_at = float(expires_at) / 1000.0
        else:
            self._expires_at = time.time() + _DEFAULT_TOKEN_TTL_SECONDS
        self._token = token
        return token

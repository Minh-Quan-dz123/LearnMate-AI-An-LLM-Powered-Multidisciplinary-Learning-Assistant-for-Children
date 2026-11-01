# ============================================================
# FILE: app/providers/openai_compat.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Adapter cho mọi nhà cung cấp tương thích OpenAI Chat Completions:
# Ollama, vLLM, LM Studio, Groq, Together...
# Cấu hình qua OPENAI_COMPAT_BASE_URL / OPENAI_COMPAT_API_KEY.
# ============================================================

import httpx

from ..config import Settings
from ..errors import (
    InvalidInputError,
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)
from .base import BaseProvider, ProviderResult


class OpenAICompatProvider(BaseProvider):
    name = "openai_compat"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.openai_compat_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.openai_compat_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(settings.request_timeout_seconds),
        )

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResult:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = await self._client.post(
                "/chat/completions", json=payload, timeout=timeout
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(
                "Không kết nối được máy chủ mô hình cục bộ. Vui lòng kiểm tra dịch vụ."
            ) from exc

        if response.status_code == 200:
            try:
                body = response.json()
                choice = body["choices"][0]
                content = choice["message"].get("content") or ""
                usage = body.get("usage") or {}
                return ProviderResult(
                    content=content,
                    model=body.get("model", model),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    finish_reason=choice.get("finish_reason"),
                )
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise LLMProviderError(
                    "Không đọc được nội dung từ nhà cung cấp mô hình."
                ) from exc

        status = response.status_code
        if status == 429:
            raise RateLimitedError()
        if status in (400, 404, 422):
            raise InvalidInputError(
                "Yêu cầu gọi mô hình không hợp lệ. Vui lòng kiểm tra cấu hình model.",
                details={"provider_status": status, "provider_detail": response.text[:500]},
            )
        if status in (401, 402, 503):
            raise LLMUnavailableError()
        raise LLMProviderError(details={"provider_status": status})

    async def close(self) -> None:
        await self._client.aclose()

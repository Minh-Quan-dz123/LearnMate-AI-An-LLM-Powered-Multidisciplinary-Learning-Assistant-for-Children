# ============================================================
# FILE: app/providers/openrouter.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Adapter gọi OpenRouter (https://openrouter.ai) qua API tương thích
# OpenAI Chat Completions.
#
# - Đọc API key từ biến môi trường (không hardcode).
# - Hỗ trợ gọi text lẫn vision (ảnh base64/URL) vì OpenRouter dùng chung
#   định dạng content array.
# - Chuyển mã HTTP lỗi của provider sang exception chuẩn hóa.
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


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        # OpenRouter khuyến nghị khai báo nguồn (tùy chọn nhưng nên có).
        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = settings.openrouter_site_url
        if settings.openrouter_app_title:
            headers["X-Title"] = settings.openrouter_app_title

        self._client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url.rstrip("/"),
            headers=headers,
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
            # Lỗi mạng / kết nối tới OpenRouter.
            raise LLMUnavailableError(
                "Không kết nối được nhà cung cấp mô hình. Vui lòng thử lại sau."
            ) from exc

        if response.status_code == 200:
            return self._parse_success(response, model)

        self._raise_for_status(response)

        # Không bao giờ tới đây (raise_for_status luôn raise).
        raise LLMProviderError()

    def _parse_success(self, response: httpx.Response, requested_model: str) -> ProviderResult:
        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError("Nhà cung cấp trả về dữ liệu không hợp lệ.") from exc

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Không đọc được nội dung từ nhà cung cấp mô hình.",
                details={"keys": list(body.keys()) if isinstance(body, dict) else None},
            ) from exc

        if content is None:
            content = ""

        usage = body.get("usage") or {}
        return ProviderResult(
            content=content,
            model=body.get("model", requested_model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            finish_reason=choice.get("finish_reason"),
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        status = response.status_code
        detail = response.text[:500]

        if status in (401, 402):
            # Sai API key hoặc hết credit OpenRouter.
            raise LLMUnavailableError(
                "Máy chủ AI chưa sẵn sàng do lỗi cấu hình nhà cung cấp. "
                "Vui lòng báo quản trị hệ thống."
            )
        if status == 429:
            raise RateLimitedError(
                "Nhà cung cấp mô hình đang giới hạn tần suất. Vui lòng thử lại sau."
            )
        if status == 400 or status == 404 or status == 422:
            # Thường do model ID sai hoặc tham số không hợp lệ -> lỗi phía ta.
            raise InvalidInputError(
                "Yêu cầu gọi mô hình không hợp lệ. Vui lòng kiểm tra lại cấu hình model.",
                details={"provider_status": status, "provider_detail": detail},
            )
        # 5xx và các mã còn lại.
        raise LLMProviderError(
            "Nhà cung cấp mô hình đang gặp lỗi. Vui lòng thử lại sau.",
            details={"provider_status": status},
        )

    async def close(self) -> None:
        await self._client.aclose()

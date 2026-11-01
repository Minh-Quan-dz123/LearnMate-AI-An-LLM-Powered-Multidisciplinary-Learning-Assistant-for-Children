# ============================================================
# FILE: app/service.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Lõi xử lý của LLM Server:
# - Ánh xạ nhãn logic -> model thật.
# - Kiểm tra kích thước prompt.
# - Giới hạn rate limit.
# - Gọi provider với RETRY (nhân lũy thừa) và TIMEOUT.
# - Trả về kết quả + metadata thống nhất (model thật, usage, latency).
#
# LLM Server KHÔNG sở hữu prompt nghiệp vụ:
# prompt sinh câu hỏi / chấm bài do EGM phía BE xây dựng.
# ============================================================

import asyncio
import time

from .config import Settings
from .errors import (
    InvalidInputError,
    LLMTimeoutError,
    RateLimitedError,
)
from .providers import BaseProvider, ProviderResult
from .rate_limit import SlidingWindowRateLimiter


class GenerationService:
    """Điều phối việc gọi model cho cả text và vision."""

    def __init__(self, settings: Settings, provider: BaseProvider) -> None:
        self.settings = settings
        self.provider = provider
        self.rate_limiter = SlidingWindowRateLimiter(
            settings.rate_limit_requests_per_minute
        )

    # --------------------------------------------------------
    # 1. KIỂM TRA ĐẦU VÀO
    # --------------------------------------------------------
    def _validate_prompt(self, prompt: str | None) -> str:
        if not prompt or not prompt.strip():
            raise InvalidInputError("Prompt không được để trống.")
        if len(prompt) > self.settings.max_prompt_chars:
            raise InvalidInputError(
                f"Prompt quá dài (tối đa {self.settings.max_prompt_chars} ký tự).",
                details={"length": len(prompt)},
            )
        return prompt.strip()

    def _build_messages(
        self, prompt: str, system_prompt: str | None = None
    ) -> list[dict]:
        messages: list[dict] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt})
        return messages

    # --------------------------------------------------------
    # 2. GỌI PROVIDER CÓ RETRY
    # --------------------------------------------------------
    async def _call_with_retry(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> tuple[ProviderResult, int]:
        """Gọi provider, thử lại tối đa settings.max_retries lần.

        Retry áp dụng cho: timeout, rate limit (429), lỗi provider (5xx).
        KHÔNG retry cho lỗi đầu vào (422) - retry vô ích.

        Trả về: (ProviderResult, số lần đã gọi).
        """
        max_attempts = 1 + max(0, self.settings.max_retries)
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = await self.provider.chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.settings.request_timeout_seconds,
                )
                return result, attempt
            except (LLMTimeoutError, RateLimitedError) as exc:
                last_error = exc
                if attempt < max_attempts:
                    # Exponential backoff: 1s, 2s, 4s...
                    await asyncio.sleep(
                        self.settings.retry_backoff_seconds * (2 ** (attempt - 1))
                    )
            except Exception:
                # Lỗi khác (502/422 từ provider...) -> không retry để tránh
                # tốn chi phí và kéo dài thời gian chờ của trẻ.
                raise

        # Hết lượt thử mà vẫn lỗi.
        assert last_error is not None
        raise last_error

    # --------------------------------------------------------
    # 3. TEXT GENERATION
    # --------------------------------------------------------
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        task: str = "Sinh nội dung",
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        prompt = self._validate_prompt(prompt)

        if not self.rate_limiter.check():
            raise RateLimitedError()

        real_model = self.settings.resolve_model(model)
        temp = (
            temperature
            if temperature is not None
            else self.settings.default_temperature
        )
        max_tokens = min(
            max_output_tokens or self.settings.default_max_output_tokens,
            self.settings.max_output_tokens_limit,
        )

        started = time.monotonic()
        result, attempts = await self._call_with_retry(
            model=real_model,
            messages=self._build_messages(prompt, system_prompt),
            temperature=temp,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.monotonic() - started) * 1000)

        return {
            "content": result.content,
            "model": result.model,
            "provider": self.provider.name,
            "task": task,
            "usage": result.usage,
            "latency_ms": latency_ms,
            "attempts": attempts,
        }

    # --------------------------------------------------------
    # 4. VISION (sau MVP, đã dựng sẵn)
    # --------------------------------------------------------
    async def generate_vision(
        self,
        prompt: str,
        image_url: str | None = None,
        image_base64: str | None = None,
        image_media_type: str | None = None,
        model: str | None = None,
        task: str = "Đánh giá hình ảnh",
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        prompt = self._validate_prompt(prompt)

        final_image_url = self._resolve_image(
            image_url, image_base64, image_media_type
        )

        if not self.rate_limiter.check():
            raise RateLimitedError()

        real_model = self.settings.resolve_model(model)
        temp = (
            temperature
            if temperature is not None
            else self.settings.default_temperature
        )
        max_tokens = min(
            max_output_tokens or self.settings.default_max_output_tokens,
            self.settings.max_output_tokens_limit,
        )

        # Định dạng OpenAI-compatible cho ảnh.
        user_content: list[dict] = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": final_image_url}},
        ]
        messages: list[dict] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_content})

        started = time.monotonic()
        result, attempts = await self._call_with_retry(
            model=real_model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.monotonic() - started) * 1000)

        return {
            "content": result.content,
            "model": result.model,
            "provider": self.provider.name,
            "task": task,
            "usage": result.usage,
            "latency_ms": latency_ms,
            "attempts": attempts,
        }

    @staticmethod
    def _resolve_image(
        image_url: str | None,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> str:
        if image_url and image_url.strip():
            url = image_url.strip()
            if url.startswith("data:"):
                return url
            if url.startswith("http://") or url.startswith("https://"):
                return url
            raise InvalidInputError(
                "image_url phải là URL http/https hoặc data URL base64."
            )

        if image_base64 and image_base64.strip():
            media = (image_media_type or "image/png").strip()
            data = image_base64.strip()
            # Hỗ trợ gửi cả data URL sẵn trong image_base64.
            if data.startswith("data:"):
                return data
            return f"data:{media};base64,{data}"

        raise InvalidInputError(
            "Cần cung cấp ảnh qua image_url hoặc image_base64."
        )

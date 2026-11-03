
# ============================================================
# FILE: app/service.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Lõi xử lý của LLM Server:
# - Chọn provider theo nhãn model.
# - Module 1-2: giữ provider cũ.
# - Module 3: dùng Gemini khi model="detective".
# - Kiểm tra prompt, rate limit, retry, timeout.
# - Trả content, model, provider, usage, latency, attempts.
#
# LLM Server KHÔNG xây prompt nghiệp vụ.
# Prompt vụ án thuộc detective_egm.py ở BE.
# ============================================================

import asyncio
import time

from .config import Settings
from .errors import (
    InvalidInputError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)
from .providers import BaseProvider, ProviderResult
from .rate_limit import SlidingWindowRateLimiter


class GenerationService:
    """
    Service điều phối text generation và vision.

    provider:
        Provider cũ của Module 1-2.

    detective_provider:
        GeminiProvider cho Module 3.

    Không chọn provider bằng task vì task chỉ phục vụ
    ghi log và mô tả tác vụ.
    """

    def __init__(
        self,
        settings: Settings,
        provider: BaseProvider,
        detective_provider: BaseProvider | None = None,
    ) -> None:
        self.settings = settings

        # Provider mặc định: Module 1-2.
        self.provider = provider

        # Provider riêng: Module 3.
        # Optional để không phá các lời gọi constructor cũ.
        self.detective_provider = detective_provider

        # Giới hạn request chung cho service.
        self.rate_limiter = SlidingWindowRateLimiter(
            settings.rate_limit_requests_per_minute
        )

    # ========================================================
    # 1. KIỂM TRA PROMPT
    # ========================================================

    def _validate_prompt(self, prompt: str | None) -> str:
        """
        Kiểm tra prompt không rỗng và không quá dài.

        Trả về prompt sau khi loại bỏ khoảng trắng đầu/cuối.
        """
        if not prompt or not prompt.strip():
            raise InvalidInputError(
                "Prompt không được để trống."
            )

        if len(prompt) > self.settings.max_prompt_chars:
            raise InvalidInputError(
                f"Prompt quá dài "
                f"(tối đa {self.settings.max_prompt_chars} ký tự).",
                details={"length": len(prompt)},
            )

        return prompt.strip()

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """
        Chuyển prompt thành danh sách message chuẩn.

        Ví dụ:
        [
            {"role": "system", "content": "Trả về JSON"},
            {"role": "user", "content": "Tạo vụ án về cây"}
        ]
        """
        messages: list[dict] = []

        if system_prompt and system_prompt.strip():
            messages.append({
                "role": "system",
                "content": system_prompt.strip(),
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        return messages

    # ========================================================
    # 2. DISPATCHER - CHỌN PROVIDER
    # ========================================================

    def _select_text_provider(
        self,
        requested_model: str | None,
    ) -> tuple[BaseProvider, str]:
        """
        Chọn provider và ID model thực tế.

        Trường hợp 1:
            requested_model="detective"

            -> GeminiProvider
            -> MODEL_DETECTIVE

        Trường hợp 2:
            requested_model="generation"/"evaluation"/...

            -> Provider cũ
            -> Settings.resolve_model()

        Không tự fallback Module 3 về provider cũ.
        """

        # ----------------------------------------------------
        # MODULE 3: THÁM TỬ KHOA HỌC
        # ----------------------------------------------------

        if (
            requested_model
            and requested_model.strip().lower() == "detective"
        ):
            if self.detective_provider is None:
                raise LLMUnavailableError(
                    "Module 3 chưa khởi tạo GeminiProvider "
                    "trong LLM Server."
                )

            real_model = self.settings.model_detective.strip()

            if not real_model:
                raise LLMUnavailableError(
                    "Thiếu MODEL_DETECTIVE trong cấu hình "
                    "LLM Server."
                )

            return self.detective_provider, real_model

        # ----------------------------------------------------
        # MODULE 1-2: GIỮ NGUYÊN
        # ----------------------------------------------------

        real_model = self.settings.resolve_model(
            requested_model
        )

        return self.provider, real_model

    # ========================================================
    # 3. GỌI PROVIDER CÓ RETRY
    # ========================================================

    async def _call_with_retry(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        provider: BaseProvider | None = None,
    ) -> tuple[ProviderResult, int]:
        """
        Gọi provider với retry theo cấu hình.

        Retry khi:
            - LLMTimeoutError
            - RateLimitedError

        Không retry lỗi đầu vào hoặc các lỗi provider
        khác, giữ chính sách của service gốc.

        Ví dụ MAX_RETRIES=2:
            Lần 1: gọi model
            Lần 2: retry nếu lỗi được phép
            Lần 3: retry cuối

        Trả về:
            (ProviderResult, so_lan_goi)
        """

        # Mỗi request dùng provider riêng.
        # Không gán lại self.provider.
        active_provider = (
            provider if provider is not None else self.provider
        )

        max_attempts = 1 + max(
            0, self.settings.max_retries
        )

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = await active_provider.chat(
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
                    delay = (
                        self.settings.retry_backoff_seconds
                        * (2 ** (attempt - 1))
                    )

                    await asyncio.sleep(delay)

            except Exception:
                # Lỗi khác không tự retry.
                raise

        # Hết lượt retry mà vẫn lỗi.
        assert last_error is not None
        raise last_error

    # ========================================================
    # 4. TEXT GENERATION
    # ========================================================

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        task: str = "Sinh nội dung",
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        """
        Sinh nội dung bằng provider thích hợp.

        Module 1-2:
            model="generation" hoặc "evaluation"

        Module 3:
            model="detective"

        Cả hai dùng chung endpoint /internal/llm/generate.
        """

        # Bước 1: kiểm tra prompt.
        prompt = self._validate_prompt(prompt)

        # Bước 2: kiểm tra rate limit.
        if not self.rate_limiter.check():
            raise RateLimitedError()

        # Bước 3: chọn provider và model thật.
        active_provider, real_model = (
            self._select_text_provider(model)
        )

        # Bước 4: cấu hình temperature.
        temp = (
            temperature
            if temperature is not None
            else self.settings.default_temperature
        )

        # Bước 5: giới hạn token.
        max_tokens = min(
            max_output_tokens
            or self.settings.default_max_output_tokens,
            self.settings.max_output_tokens_limit,
        )

        # Bước 6: gọi provider và đo thời gian.
        started = time.monotonic()

        result, attempts = await self._call_with_retry(
            model=real_model,
            messages=self._build_messages(
                prompt,
                system_prompt,
            ),
            temperature=temp,
            max_tokens=max_tokens,
            provider=active_provider,
        )

        latency_ms = int(
            (time.monotonic() - started) * 1000
        )

        # Bước 7: trả dữ liệu chuẩn cho FastAPI.
        return {
            "content": result.content,
            "model": result.model,
            "provider": active_provider.name,
            "task": task,
            "usage": result.usage,
            "latency_ms": latency_ms,
            "attempts": attempts,
        }

    # ========================================================
    # 5. VISION - GIỮ NGUYÊN CHỨC NĂNG CŨ
    # ========================================================

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
        """
        Phân tích ảnh thành nội dung text.

        Đây là API vision hiện tại, KHÔNG phải API
        sinh ảnh Cloudflare.
        """

        prompt = self._validate_prompt(prompt)

        # Module 3 V3:
        # Gửi chính ảnh Cloudflare đã sinh sang Gemini Vision.
        # Không đi qua provider chỉ hỗ trợ text.
        if task == "detective_hint_localization":
            if not self.rate_limiter.check():
                raise RateLimitedError()

            from .providers.gemini_vision import recognize

            return await recognize(
                self.settings,
                prompt=prompt,
                image_base64=image_base64,
                image_media_type=image_media_type,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                task=task,
            )


        final_image_url = self._resolve_image(
            image_url,
            image_base64,
            image_media_type,
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
            max_output_tokens
            or self.settings.default_max_output_tokens,
            self.settings.max_output_tokens_limit,
        )

        # Định dạng OpenAI-compatible cho ảnh.
        user_content: list[dict] = [
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": final_image_url,
                },
            },
        ]

        messages: list[dict] = []

        if system_prompt and system_prompt.strip():
            messages.append({
                "role": "system",
                "content": system_prompt.strip(),
            })

        messages.append({
            "role": "user",
            "content": user_content,
        })

        started = time.monotonic()

        # Vision vẫn gọi provider cũ.
        result, attempts = await self._call_with_retry(
            model=real_model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tokens,
        )

        latency_ms = int(
            (time.monotonic() - started) * 1000
        )

        return {
            "content": result.content,
            "model": result.model,
            "provider": self.provider.name,
            "task": task,
            "usage": result.usage,
            "latency_ms": latency_ms,
            "attempts": attempts,
        }

    # ========================================================
    # 6. CHUẨN HÓA ẢNH ĐẦU VÀO VISION
    # ========================================================

    @staticmethod
    def _resolve_image(
        image_url: str | None,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> str:
        """
        Chuyển URL hoặc Base64 thành dữ liệu ảnh
        có thể gửi cho provider vision.
        """

        if image_url and image_url.strip():
            url = image_url.strip()

            if url.startswith("data:"):
                return url

            if (
                url.startswith("http://")
                or url.startswith("https://")
            ):
                return url

            raise InvalidInputError(
                "image_url phải là URL http/https "
                "hoặc data URL base64."
            )

        if image_base64 and image_base64.strip():
            media = (
                image_media_type or "image/png"
            ).strip()

            data = image_base64.strip()

            if data.startswith("data:"):
                return data

            return f"data:{media};base64,{data}"

        raise InvalidInputError(
            "Cần cung cấp ảnh qua image_url "
            "hoặc image_base64."
        )

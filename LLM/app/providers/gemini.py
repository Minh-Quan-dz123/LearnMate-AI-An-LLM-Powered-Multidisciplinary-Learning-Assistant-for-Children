
# ============================================================
# FILE: app/providers/gemini.py
# MỤC ĐÍCH:
# Adapter gọi Gemini API để sinh JSON vụ án Thám tử khoa học.
#
# - Tuân theo BaseProvider.chat() của LLM Server hiện tại.
# - Dùng HTTPX bất đồng bộ, không cần thêm google-genai.
# - Chuyển system/user/assistant message sang định dạng Gemini.
# - Chuẩn hóa phản hồi thành ProviderResult.
# - Chuyển lỗi HTTP thành exception trong app/errors.py.
#
# LƯU Ý:
# - Provider chỉ gọi model và trả nội dung dạng chuỗi.
# - Detective EGM phía BE mới kiểm tra JSON và luật chơi.
# - Chưa đăng ký provider này trong service.py / config.py.
# ============================================================

import httpx

from ..errors import (
    InvalidInputError,
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)
from .base import BaseProvider, ProviderResult


class GeminiProvider(BaseProvider):
    """Adapter Gemini cho tác vụ sinh kịch bản JSON của Module 3."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        default_timeout: float = 60.0,
    ) -> None:
        # Nhận key qua tham số; không đọc .env/hardcode key tại adapter.
        if not api_key or not api_key.strip():
            raise LLMUnavailableError(
                "Chưa cấu hình GEMINI_API_KEY cho Module 3."
            )

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "x-goog-api-key": api_key.strip(),
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(default_timeout),
        )

    @staticmethod
    def _convert_messages(messages: list[dict]) -> tuple[list[dict], str]:
        """Đổi message OpenAI-style sang contents + systemInstruction của Gemini.

        Ví dụ:
            [{"role": "system", "content": "Trả JSON"},
             {"role": "user", "content": "Tạo vụ án về cây"}]

        -> contents=[{"role": "user", "parts": [{"text": "..."}]}]
           system_instruction="Trả JSON"
        """
        contents: list[dict] = []
        system_parts: list[str] = []

        for message in messages:
            if not isinstance(message, dict):
                raise InvalidInputError(
                    "Định dạng message gửi Gemini không hợp lệ."
                )

            role = message.get("role")
            text = message.get("content")

            # Module 3 chỉ gọi text-to-text. Ảnh dùng Cloudflare riêng.
            if not isinstance(text, str) or not text.strip():
                raise InvalidInputError(
                    "GeminiProvider hiện chỉ hỗ trợ message chứa văn bản."
                )

            if role == "system":
                system_parts.append(text.strip())

            elif role in ("user", "assistant", "model"):
                contents.append(
                    {
                        "role": (
                            "model"
                            if role in ("assistant", "model")
                            else "user"
                        ),
                        "parts": [{"text": text.strip()}],
                    }
                )

            else:
                raise InvalidInputError(
                    f"Role không được hỗ trợ: {role}"
                )

        if not contents:
            raise InvalidInputError(
                "Cần có ít nhất một message user/model."
            )

        return contents, "\n\n".join(system_parts)

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResult:
        """Gọi Gemini generateContent và trả ProviderResult."""

        if not isinstance(model, str) or not model.strip():
            raise InvalidInputError("Chưa xác định model Gemini.")

        contents, system_instruction = self._convert_messages(messages)

        # Cấu trúc payload của Gemini REST API.
        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,

                # Gemini sinh JSON cho kịch bản Thám tử khoa học.
                "responseMimeType": "application/json",
            },
        }

        # Chỉ thêm systemInstruction khi có system prompt.
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = await self._client.post(
                f"/models/{model.strip()}:generateContent",
                json=payload,
                timeout=timeout,
            )

        except httpx.TimeoutException as exc:
            raise LLMTimeoutError() from exc

        except httpx.HTTPError as exc:
            raise LLMUnavailableError(
                "Không kết nối được Gemini API. Vui lòng thử lại sau."
            ) from exc

        # Phản hồi lỗi HTTP phải chuyển sang exception chung.
        if response.status_code != 200:
            self._raise_for_status(response.status_code)

        # Phản hồi thành công -> ProviderResult.
        return self._parse_success(response, model.strip())

    @staticmethod
    def _parse_success(
        response: httpx.Response,
        requested_model: str,
    ) -> ProviderResult:
        """Trích nội dung, usage và finish reason từ Gemini."""

        try:
            body = response.json()

            # Gemini trả candidates chứa các kết quả được sinh.
            candidate = body["candidates"][0]
            parts = candidate["content"]["parts"]

            # Ghép các đoạn text trả về thành một chuỗi.
            content = "".join(
                part["text"]
                for part in parts
                if isinstance(part, dict)
                and isinstance(part.get("text"), str)
            )

            if not content.strip():
                raise ValueError("Gemini trả về nội dung rỗng.")

            # Thống kê số token mà Gemini đã sử dụng.
            usage = body.get("usageMetadata") or {}

            return ProviderResult(
                content=content,
                model=body.get("modelVersion") or requested_model,
                usage={
                    "prompt_tokens": usage.get("promptTokenCount"),
                    "completion_tokens": usage.get("candidatesTokenCount"),
                    "total_tokens": usage.get("totalTokenCount"),
                },
                finish_reason=candidate.get("finishReason"),
            )

        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            AttributeError,
        ) as exc:
            raise LLMProviderError(
                "Gemini không trả về nội dung có thể sử dụng."
            ) from exc

    @staticmethod
    def _raise_for_status(status: int) -> None:
        """Ánh xạ HTTP status của Google vào hệ thống lỗi chung."""

        if status in (401, 403):
            # Key sai, bị báo lộ hoặc thiếu quyền gọi model.
            raise LLMUnavailableError(
                "Gemini từ chối truy cập. "
                "Kiểm tra GEMINI_API_KEY và quyền gọi model."
            )

        if status == 429:
            raise RateLimitedError(
                "Gemini đang giới hạn lượt gọi. Vui lòng thử lại sau."
            )

        if status in (400, 404, 422):
            raise InvalidInputError(
                "Yêu cầu gửi Gemini không hợp lệ. "
                "Kiểm tra model và tham số.",
                details={"provider_status": status},
            )

        if status in (408, 504):
            raise LLMTimeoutError()

        raise LLMProviderError(
            "Gemini gặp lỗi khi tạo nội dung. Vui lòng thử lại.",
            details={"provider_status": status},
        )

    async def close(self) -> None:
        """Đóng HTTP client khi LLM Server dừng."""
        await self._client.aclose()

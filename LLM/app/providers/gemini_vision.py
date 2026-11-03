
"""
Gemini Vision cho Module 3 V3.

BE gửi ảnh Cloudflare dạng base64.
LLM Server chuyển ảnh thành inlineData của Gemini.

MODEL_VISION được đọc từ Settings.
Không hardcode model hoặc API key.
"""

import base64
import binascii
import time

import httpx

from ..errors import (
    InvalidInputError,
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)


def decode_image(
    image_base64: str | None,
    mime: str | None,
) -> bytes:
    """Kiểm tra MIME, kích thước và magic bytes."""

    if mime not in ("image/png", "image/jpeg"):
        raise InvalidInputError(
            "Gemini Vision chỉ nhận PNG/JPEG."
        )

    if (
        not image_base64
        or len(image_base64) > 14 * 1024 * 1024
    ):
        raise InvalidInputError(
            "Thiếu ảnh hoặc ảnh quá lớn."
        )

    try:
        image = base64.b64decode(
            image_base64,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise InvalidInputError(
            "Ảnh base64 không hợp lệ."
        ) from exc

    if (
        len(image) == 0
        or len(image) > 10 * 1024 * 1024
    ):
        raise InvalidInputError(
            "Kích thước ảnh không hợp lệ."
        )

    if (
        mime == "image/png"
        and not image.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise InvalidInputError(
            "Ảnh PNG không khớp MIME."
        )

    if (
        mime == "image/jpeg"
        and not image.startswith(b"\xff\xd8\xff")
    ):
        raise InvalidInputError(
            "Ảnh JPEG không khớp MIME."
        )

    return image


async def recognize(
    settings,
    *,
    prompt: str,
    image_base64: str | None,
    image_media_type: str | None,
    max_output_tokens: int | None,
    temperature: float | None,
    task: str,
) -> dict:
    """
    Gửi ảnh thật qua Gemini generateContent API.

    Input:
        prompt
        image_base64
        image_media_type

    Output:
        Dictionary tương thích VisionResponse.
    """

    image = decode_image(
        image_base64,
        image_media_type,
    )

    if (
        not settings.gemini_api_key
        or not settings.model_detective.strip()
    ):
        raise LLMUnavailableError(
            "Chưa cấu hình GEMINI_API_KEY hoặc MODEL_DETECTIVE."
        )

    # Dùng model Gemini đã cấu hình sẵn cho Module 3.
    model = settings.model_detective.strip()

    # Chuẩn hóa nếu tên model có tiền tố "models/".
    # API bên dưới tự thêm "/models/" vào URL.
    if model.startswith("models/"):
        model = model.removeprefix("models/")

    # Không cho phép model ID chứa đường dẫn hoặc query tùy ý.
    import re

    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise InvalidInputError(
            "MODEL_DETECTIVE không phải Gemini model ID hợp lệ."
        )


    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    },
                    {
                        "inlineData": {
                            "mimeType": image_media_type,
                            "data": base64.b64encode(
                                image
                            ).decode("ascii"),
                        },
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": (
                0.1
                if temperature is None
                else temperature
            ),
            "maxOutputTokens": min(
                max_output_tokens or 1800,
                settings.max_output_tokens_limit,
            ),
            "responseMimeType": "application/json",
        },
    }

    url = (
        settings.gemini_base_url.rstrip("/")
        + f"/models/{model}:generateContent"
    )

    started = time.monotonic()

    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds
        ) as client:

            response = await client.post(
                url,
                headers={
                    "x-goog-api-key":
                        settings.gemini_api_key,
                    "Content-Type":
                        "application/json",
                },
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise LLMTimeoutError() from exc

    except httpx.HTTPError as exc:
        raise LLMUnavailableError() from exc

    if response.status_code == 429:
        raise RateLimitedError()

    if response.status_code in (401, 403, 404):
        raise LLMUnavailableError(
            "Gemini Vision chưa có quyền dùng "
            "model hoặc API key không hợp lệ."
        )

    if response.status_code >= 500:
        raise LLMUnavailableError(
            "Gemini Vision đang tạm thời gián đoạn."
        )

    if response.status_code >= 400:
        raise LLMProviderError(
            "Gemini Vision từ chối dữ liệu "
            "hoặc model không hỗ trợ ảnh."
        )

    try:
        body = response.json()

        parts = (
            body["candidates"][0]
                ["content"]["parts"]
        )

        content = "".join(
            item.get("text", "")
            for item in parts
            if isinstance(item, dict)
        )

        if not content:
            raise ValueError(
                "Không có nội dung phản hồi"
            )

    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError,
    ) as exc:
        raise LLMProviderError(
            "Gemini Vision trả dữ liệu không hợp lệ."
        ) from exc

    usage = body.get("usageMetadata") or {}

    return {
        "content": content,
        "model": model,
        "provider": "gemini",
        "task": task,
        "usage": {
            "prompt_tokens":
                usage.get("promptTokenCount"),
            "completion_tokens":
                usage.get("candidatesTokenCount"),
            "total_tokens":
                usage.get("totalTokenCount"),
        },
        "latency_ms": int(
            (time.monotonic() - started) * 1000
        ),
        "attempts": 1,
    }

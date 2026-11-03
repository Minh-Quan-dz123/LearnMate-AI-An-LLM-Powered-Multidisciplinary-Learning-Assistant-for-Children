
"""
FILE: LLM/app/providers/gemini_speech.py

Module 3 — Gemini TTS.

Chức năng:
1. Nhận văn bản tiếng Việt.
2. Gọi Gemini Interactions REST API.
3. Đọc audio từ response.
4. Chuẩn hóa thành WAV.
5. Trả bytes cho LLM Server.

Không sử dụng Gemini SDK; chỉ cần httpx hiện có.
"""

from __future__ import annotations

import base64
import binascii
import io
import re
import wave

import httpx

from app.errors import (
    InvalidInputError,
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)

MAX_AUDIO_BYTES = 8 * 1024 * 1024


def pcm_to_wav(
    pcm: bytes,
    rate: int = 24000,
) -> bytes:
    """
    Đóng gói dữ liệu PCM16 mono thành WAV.

    Dùng khi nhà cung cấp trả audio/l16
    thay vì WAV có header.
    """
    if (
        not pcm
        or len(pcm) % 2
        or len(pcm) > MAX_AUDIO_BYTES
    ):
        raise LLMProviderError(
            "Dữ liệu âm thanh PCM không hợp lệ."
        )

    if not 8000 <= rate <= 96000:
        raise LLMProviderError(
            "Tần số lấy mẫu không hợp lệ."
        )

    result = io.BytesIO()

    with wave.open(result, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)

    return result.getvalue()


def _extract_audio(response_json: dict) -> dict:
    """
    Đọc audio trong response REST.

    Cấu trúc:
    steps[] -> content[] -> type='audio'

    Giữ tương thích với response dạng cũ
    có trường output_audio.
    """
    steps = response_json.get("steps", [])

    if isinstance(steps, list):
        for step in reversed(steps):
            if not isinstance(step, dict):
                continue

            contents = step.get("content", [])

            if not isinstance(contents, list):
                continue

            for part in reversed(contents):
                if (
                    isinstance(part, dict)
                    and part.get("type") == "audio"
                ):
                    return part

    audio = response_json.get("output_audio")

    if isinstance(audio, dict):
        return audio

    raise LLMProviderError(
        "Gemini TTS không trả dữ liệu âm thanh."
    )


async def generate_speech(
    *,
    base_url: str,
    api_key: str,
    model: str,
    voice: str,
    text: str,
    timeout: float,
) -> bytes:
    """
    Gửi văn bản tới Gemini TTS và nhận WAV.

    Ví dụ:
        text = "Chào các thám tử nhí!"
        model = "gemini-3.8-flash-lite-tts"
        voice = "Aoede"
    """
    if not api_key or not model:
        raise LLMUnavailableError(
            "Chưa cấu hình Gemini TTS."
        )

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_-]{1,59}",
        voice,
    ):
        raise InvalidInputError(
            "Tên giọng TTS không hợp lệ."
        )

    if not text or not text.strip():
        raise InvalidInputError(
            "Nội dung cần đọc không được trống."
        )

    # Request theo Interactions API.
    # Nội dung cần đọc nằm trong user_input.
    payload = {
        "model": model,
        "input": [
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "annotations": [
                            {
                                "type": "speech_metadata",
                                "style": (
                                    "Warm Vietnamese female teacher, "
                                    "clear pronunciation, "
                                    "gentle cheerful tone, "
                                    "natural pace. Read verbatim."
                                ),
                            }
                        ],
                    }
                ],
            }
        ],
        "response_format": {
            "type": "audio",
        },
        "generation_config": {
            "speech_config": [
                {
                    "voice": voice,
                }
            ],
        },
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/interactions",
                headers={
                    "x-goog-api-key": api_key,
                },
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise LLMTimeoutError(
            "Gemini TTS phản hồi quá lâu."
        ) from exc

    except httpx.HTTPError as exc:
        raise LLMUnavailableError(
            "Không kết nối được Gemini TTS."
        ) from exc

    if response.status_code == 429:
        raise RateLimitedError(
            "Gemini TTS hết quota hoặc đang bị giới hạn."
        )

    if response.status_code in (401, 403, 404):
        raise LLMUnavailableError(
            "API key/model Gemini TTS không khả dụng."
        )

    if response.status_code >= 500:
        raise LLMUnavailableError(
            "Gemini TTS đang bận."
        )

    if response.status_code != 200:
        raise LLMProviderError(
            "Gemini TTS không tạo được âm thanh."
        )

    try:
        audio = _extract_audio(response.json())
        encoded = audio.get("data")

        if (
            not isinstance(encoded, str)
            or len(encoded) > MAX_AUDIO_BYTES * 2
        ):
            raise ValueError(
                "Dữ liệu base64 audio không hợp lệ."
            )

        raw = base64.b64decode(
            encoded,
            validate=True,
        )

        if len(raw) > MAX_AUDIO_BYTES:
            raise ValueError(
                "Audio vượt quá dung lượng cho phép."
            )

        # Trường hợp trả WAV hoàn chỉnh.
        if (
            raw.startswith(b"RIFF")
            and raw[8:12] == b"WAVE"
        ):
            return raw

        # Chỉ đóng gói thành WAV nếu MIME là PCM.
        mime = audio.get("mime_type")

        if mime not in ("audio/l16", "audio/pcm"):
            raise ValueError(
                "Định dạng audio không phải WAV/PCM."
            )

        rate = int(audio.get("sample_rate", 24000))

        return pcm_to_wav(
            raw,
            rate,
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        binascii.Error,
    ) as exc:
        raise LLMProviderError(
            "Gemini TTS trả audio không hợp lệ."
        ) from exc

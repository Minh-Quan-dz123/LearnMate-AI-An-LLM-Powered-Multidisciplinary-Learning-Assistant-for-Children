
# ============================================================
# FILE: tests/test_detective_dispatcher.py
#
# MỤC ĐÍCH:
# Kiểm thử điều phối provider của GenerationService.
#
# - Module 3 chọn Gemini.
# - Module 1-2 giữ provider cũ.
# - Thiếu provider/model phải báo lỗi.
# - Vision giữ provider cũ.
# - Retry không chuyển nhầm provider.
#
# Không gọi API thật.
# ============================================================

import asyncio

import pytest

from app.config import Settings
from app.errors import LLMUnavailableError, RateLimitedError
from app.providers.base import BaseProvider, ProviderResult
from app.service import GenerationService


class SpyProvider(BaseProvider):
    """
    Provider giả dùng trong unit test.

    Mỗi lần gọi chat(), lưu tham số vào self.calls.
    Nhờ vậy test biết request đã đi vào provider nào.
    """

    def __init__(
        self,
        name: str,
        fail_once: bool = False,
    ):
        self.name = name
        self.calls = []
        self.fail_once = fail_once

    async def chat(
        self,
        model,
        messages,
        temperature,
        max_tokens,
        timeout,
    ):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        })

        # Mô phỏng bị rate limit ở lần gọi đầu.
        if self.fail_once and len(self.calls) == 1:
            raise RateLimitedError("Thử lại")

        return ProviderResult(
            content='{"ok":true}',
            model=model,
            usage={},
        )


def make_settings(**overrides):
    """Tạo Settings độc lập cho từng bài test."""

    values = {
        "model_generation": "old/generation",
        "model_evaluation": "old/evaluation",
        "model_vision": "old/vision",
        "model_default": "old/default",
        "model_detective": "gemini-test-model",
        "rate_limit_requests_per_minute": 100,
        "max_retries": 0,
    }

    values.update(overrides)

    return Settings(**values)


# ============================================================
# TEST 1: MODULE 3 PHẢI CHỌN GEMINI
# ============================================================

def test_detective_routes_to_gemini():
    old = SpyProvider("old")
    gemini = SpyProvider("gemini")

    service = GenerationService(
        make_settings(),
        old,
        gemini,
    )

    async def run():
        return await service.generate(
            prompt="Tạo vụ án",
            model="DETECTIVE",
            task="detective_case_generation",
            temperature=0.6,
            max_output_tokens=4000,
        )

    data = asyncio.run(run())

    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-test-model"
    assert data["attempts"] == 1

    assert len(gemini.calls) == 1
    assert gemini.calls[0]["max_tokens"] == 4000
    assert old.calls == []


# ============================================================
# TEST 2-6: CÁC NHÃN MODEL CŨ
# ============================================================

@pytest.mark.parametrize(
    "alias,expected",
    [
        ("generation", "old/generation"),
        ("evaluation", "old/evaluation"),
        ("vision", "old/vision"),
        ("unknown-label", "old/default"),
        (None, "old/default"),
    ],
)
def test_old_routes_unchanged(alias, expected):
    old = SpyProvider("old")
    gemini = SpyProvider("gemini")

    service = GenerationService(
        make_settings(),
        old,
        gemini,
    )

    async def run():
        return await service.generate(
            prompt="Xin chào",
            model=alias,
        )

    data = asyncio.run(run())

    assert data["provider"] == "old"
    assert data["model"] == expected

    assert len(old.calls) == 1
    assert gemini.calls == []


# ============================================================
# TEST 7: TASK KHÔNG TỰ ĐỔI PROVIDER
# ============================================================

def test_task_name_does_not_switch_provider():
    old = SpyProvider("old")
    gemini = SpyProvider("gemini")

    service = GenerationService(
        make_settings(),
        old,
        gemini,
    )

    async def run():
        return await service.generate(
            prompt="Xin chào",
            model="generation",
            task="detective_case_generation",
        )

    data = asyncio.run(run())

    assert data["provider"] == "old"
    assert gemini.calls == []


# ============================================================
# TEST 8: THIẾU GEMINI PROVIDER
# ============================================================

def test_missing_detective_provider_never_falls_back():
    old = SpyProvider("old")

    service = GenerationService(
        make_settings(),
        old,
    )

    async def run():
        with pytest.raises(LLMUnavailableError):
            await service.generate(
                prompt="Tạo vụ án",
                model="detective",
            )

    asyncio.run(run())

    assert old.calls == []


# ============================================================
# TEST 9: THIẾU MODEL_DETECTIVE
# ============================================================

def test_missing_detective_model_never_falls_back():
    old = SpyProvider("old")
    gemini = SpyProvider("gemini")

    service = GenerationService(
        make_settings(model_detective=""),
        old,
        gemini,
    )

    async def run():
        with pytest.raises(LLMUnavailableError):
            await service.generate(
                prompt="Tạo vụ án",
                model="detective",
            )

    asyncio.run(run())

    assert old.calls == []
    assert gemini.calls == []


# ============================================================
# TEST 10: VISION VẪN CHỌN PROVIDER CŨ
# ============================================================

def test_vision_still_uses_old_provider():
    old = SpyProvider("old")
    gemini = SpyProvider("gemini")

    service = GenerationService(
        make_settings(),
        old,
        gemini,
    )

    async def run():
        return await service.generate_vision(
            prompt="Đánh giá ảnh",
            image_base64="aGVsbG8=",
            image_media_type="image/png",
            model="vision",
        )

    data = asyncio.run(run())

    assert data["provider"] == "old"
    assert old.calls[0]["model"] == "old/vision"
    assert gemini.calls == []


# ============================================================
# TEST 11: RETRY ĐÚNG PROVIDER ĐÃ CHỌN
# ============================================================

def test_retry_uses_selected_provider_only():
    old = SpyProvider("old")

    # Gemini giả bị rate limit ở lần gọi đầu.
    gemini = SpyProvider(
        "gemini",
        fail_once=True,
    )

    settings = make_settings(
        max_retries=1,
        retry_backoff_seconds=0,
    )

    service = GenerationService(
        settings,
        old,
        gemini,
    )

    async def run():
        return await service.generate(
            prompt="Tạo vụ án",
            model="detective",
        )

    data = asyncio.run(run())

    # Lần đầu lỗi, lần thứ hai thành công.
    assert data["attempts"] == 2

    assert len(gemini.calls) == 2
    assert old.calls == []


# ============================================================
# FILE: tests/test_cloudflare_provider.py
# Unit test provider bằng HTTPX MockTransport.
# Không gọi Cloudflare thật, không tốn API quota.
# Chạy từ thư mục LLM/: python -m pytest tests/test_cloudflare_provider.py -v
# ============================================================

import asyncio
import base64
import json

import httpx
import pytest

from app.errors import (
    InvalidInputError,
    LLMProviderError,
    LLMUnavailableError,
    RateLimitedError,
)
from app.providers.cloudflare import CloudflareImageProvider


# Một payload PNG nhỏ chỉ dùng để kiểm tra header/Base64.
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"
MODEL = "@cf/black-forest-labs/flux-1-schnell"


def make_provider(handler):
    """Thay mạng thật bằng một hàm trả HTTP response giả lập."""
    return CloudflareImageProvider(
        account_id="testaccount",
        api_token="token-for-testing-only",
        transport=httpx.MockTransport(handler),
    )


def test_generate_image_success():
    """Request đúng và response Base64 được chuẩn hóa thành MIME PNG."""
    def handler(request: httpx.Request):
        assert request.method == "POST"
        assert request.url.path.endswith(f"/ai/run/{MODEL}")
        assert request.headers["Authorization"] == "Bearer token-for-testing-only"
        payload = json.loads(request.content)
        assert payload == {"prompt": "Happy classroom", "steps": 4}
        return httpx.Response(
            200,
            json={
                "success": True,
                "result": {"image": base64.b64encode(FAKE_PNG).decode("ascii")},
            },
        )

    async def run():
        provider = make_provider(handler)
        try:
            result = await provider.generate_image(MODEL, "Happy classroom")
            assert result.mime_type == "image/png"
            assert result.provider == "cloudflare"
            assert result.model == MODEL
            assert base64.b64decode(result.image_base64) == FAKE_PNG
        finally:
            await provider.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "status,expected_error",
    [
        (403, LLMUnavailableError),
        (429, RateLimitedError),
        (400, InvalidInputError),
        (500, LLMProviderError),
    ],
)
def test_http_errors(status, expected_error):
    """Lỗi Cloudflare phải dùng hệ thống exception chung."""
    async def run():
        provider = make_provider(lambda _: httpx.Response(status))
        try:
            with pytest.raises(expected_error):
                await provider.generate_image(MODEL, "Happy classroom")
        finally:
            await provider.close()

    asyncio.run(run())


def test_invalid_base64():
    """HTTP 200 chưa đủ: ảnh lỗi Base64 phải bị từ chối."""
    async def run():
        provider = make_provider(
            lambda _: httpx.Response(200, json={"success": True, "result": {"image": "!!!"}})
        )
        try:
            with pytest.raises(LLMProviderError):
                await provider.generate_image(MODEL, "Happy classroom")
        finally:
            await provider.close()

    asyncio.run(run())


def test_validate_prompt_and_steps():
    """Dữ liệu sai được chặn trước khi phát sinh request HTTP."""
    def handler(_):
        raise AssertionError("Không được gọi mạng")

    async def run():
        provider = make_provider(handler)
        try:
            with pytest.raises(InvalidInputError):
                await provider.generate_image(MODEL, "")
            with pytest.raises(InvalidInputError):
                await provider.generate_image(MODEL, "x" * 2049)
            with pytest.raises(InvalidInputError):
                await provider.generate_image(MODEL, "Happy classroom", steps=9)
        finally:
            await provider.close()

    asyncio.run(run())

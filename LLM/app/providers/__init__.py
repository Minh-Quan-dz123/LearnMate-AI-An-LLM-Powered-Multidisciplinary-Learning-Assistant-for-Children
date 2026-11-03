
# ============================================================
# FILE: app/providers/__init__.py
# MỤC ĐÍCH:
# Khởi tạo provider phù hợp cho từng nhóm tác vụ.
#
# 1. build_provider():
#    Giữ nguyên provider chung của Module 1-2.
#
# 2. build_detective_provider():
#    Tạo Gemini provider cho Module 3.
#
# 3. build_image_provider():
#    Tạo Cloudflare provider để sinh ảnh nền.
#
# Không đổi PROVIDER toàn cục sang Gemini.
# ============================================================

from ..config import Settings
from ..errors import LLMUnavailableError

from .base import BaseProvider, ProviderResult
from .mock import MockProvider
from .openai_compat import OpenAICompatProvider
from .openrouter import OpenRouterProvider

# Hai provider đã viết ở đợt trước.
from .gemini import GeminiProvider
from .cloudflare import CloudflareImageProvider, ImageProviderResult


__all__ = [
    "BaseProvider",
    "ProviderResult",
    "MockProvider",
    "OpenRouterProvider",
    "OpenAICompatProvider",
    "GeminiProvider",
    "CloudflareImageProvider",
    "ImageProviderResult",
    "build_provider",
    "build_detective_provider",
    "build_image_provider",
]


# ============================================================
# 1. PROVIDER CŨ - MODULE 1 VÀ MODULE 2
# ============================================================

def build_provider(settings: Settings) -> BaseProvider:
    """
    Factory ban đầu của LLM Server.

    GIỮ NGUYÊN hành vi:
        MOCK_MODE=true       -> MockProvider
        PROVIDER=mock        -> MockProvider
        PROVIDER=openai_compat -> OpenAICompatProvider
        PROVIDER=openrouter  -> OpenRouterProvider

    Nếu thiếu OpenRouter API key, dùng MockProvider
    theo chính sách demo của server hiện tại.
    """

    provider = settings.provider.strip().lower()

    if settings.mock_mode:
        return MockProvider()

    if provider == "mock":
        return MockProvider()

    if provider == "openai_compat":
        return OpenAICompatProvider(settings)

    # Giữ nguyên hành vi fallback của code gốc.
    if not settings.openrouter_api_key:
        return MockProvider()

    return OpenRouterProvider(settings)


# ============================================================
# 2. GEMINI PROVIDER - MODULE 3
# ============================================================

def build_detective_provider(settings: Settings) -> BaseProvider:
    """
    Khởi tạo provider sinh kịch bản Thám tử khoa học.

    Luồng:
        Settings
           |
           v
        Kiểm tra MOCK_MODE
           |
           v
        Kiểm tra PROVIDER_DETECTIVE
           |
           v
        Kiểm tra MODEL_DETECTIVE + GEMINI_API_KEY
           |
           v
        GeminiProvider

    KHÔNG fallback sang OpenRouter nếu thiếu Gemini API key.
    """

    # Chế độ mock toàn hệ thống.
    if settings.mock_mode:
        return MockProvider()

    provider_name = settings.provider_detective.strip().lower()

    if provider_name != "gemini":
        raise LLMUnavailableError(
            "PROVIDER_DETECTIVE phải là 'gemini'."
        )

    # Kiểm tra ID model.
    if not settings.model_detective.strip():
        raise LLMUnavailableError(
            "Thiếu MODEL_DETECTIVE trong .env."
        )

    # Kiểm tra API key.
    if not settings.gemini_api_key.strip():
        raise LLMUnavailableError(
            "Thiếu GEMINI_API_KEY trong .env."
        )

    # Khởi tạo adapter Gemini.
    return GeminiProvider(
        api_key=settings.gemini_api_key,
        base_url=settings.gemini_base_url,
        default_timeout=settings.request_timeout_seconds,
    )


# ============================================================
# 3. CLOUDFLARE PROVIDER - MODULE 3
# ============================================================

def build_image_provider(
    settings: Settings,
) -> CloudflareImageProvider | None:
    """
    Khởi tạo provider tạo ảnh.

    Luồng:
        Settings
           |
           v
        Kiểm tra MOCK_MODE
           |
           v
        Kiểm tra PROVIDER_IMAGE
           |
           v
        Kiểm tra MODEL_IMAGE
           |
           v
        Kiểm tra CLOUDFLARE_ACCOUNT_ID / API_TOKEN
           |
           v
        CloudflareImageProvider

    Khi MOCK_MODE=true:
        Trả None, không kết nối Cloudflare.

    Mock ảnh sẽ được xử lý riêng ở Image Service
    trong bước triển khai API tạo ảnh.
    """

    if settings.mock_mode:
        return None

    provider_name = settings.provider_image.strip().lower()

    if provider_name != "cloudflare":
        raise LLMUnavailableError(
            "PROVIDER_IMAGE phải là 'cloudflare'."
        )

    # Kiểm tra model tạo ảnh.
    if not settings.model_image.strip():
        raise LLMUnavailableError(
            "Thiếu MODEL_IMAGE trong .env."
        )

    # Kiểm tra Cloudflare Account ID.
    if not settings.cloudflare_account_id.strip():
        raise LLMUnavailableError(
            "Thiếu CLOUDFLARE_ACCOUNT_ID trong .env."
        )

    # Kiểm tra Cloudflare API Token.
    if not settings.cloudflare_api_token.strip():
        raise LLMUnavailableError(
            "Thiếu CLOUDFLARE_API_TOKEN trong .env."
        )

    # Khởi tạo adapter Cloudflare.
    return CloudflareImageProvider(
        account_id=settings.cloudflare_account_id,
        api_token=settings.cloudflare_api_token,
        default_timeout=settings.image_timeout_seconds,
    )

# ============================================================
# FILE: app/providers/__init__.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Factory chọn provider theo cấu hình SETTINGS_PROVIDER.
# ============================================================

from ..config import Settings
from .base import BaseProvider, ProviderResult
from .mock import MockProvider
from .openai_compat import OpenAICompatProvider
from .openrouter import OpenRouterProvider

__all__ = [
    "BaseProvider",
    "ProviderResult",
    "MockProvider",
    "OpenRouterProvider",
    "OpenAICompatProvider",
    "build_provider",
]


def build_provider(settings: Settings) -> BaseProvider:
    """Tạo provider instance theo cấu hình.

    Thứ tự ưu tiên:
    1. MOCK_MODE=true -> MockProvider.
    2. PROVIDER=openrouter (mặc định).
    3. PROVIDER=openai_compat.
    4. PROVIDER=mock.
    """
    provider = settings.provider.strip().lower()

    if settings.mock_mode:
        return MockProvider()

    if provider == "mock":
        return MockProvider()

    if provider == "openai_compat":
        return OpenAICompatProvider(settings)

    # Mặc định: openrouter. Nếu thiếu key thì rơi về mock để demo không sập.
    if not settings.openrouter_api_key:
        return MockProvider()
    return OpenRouterProvider(settings)

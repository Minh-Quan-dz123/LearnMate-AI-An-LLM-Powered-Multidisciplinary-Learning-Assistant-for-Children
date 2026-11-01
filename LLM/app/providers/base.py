# ============================================================
# FILE: app/providers/base.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Interface chung cho mọi nhà cung cấp model (provider).
# Mọi adapter phải trả về ProviderResult hoặc raise exception
# đã được chuẩn hóa trong app/errors.py.
# ============================================================

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderResult:
    """Kết quả chuẩn hóa từ nhà cung cấp model."""

    content: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: str | None = None


class BaseProvider(ABC):
    """Nhà cung cấp model. Tên class dùng để log trong response."""

    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResult:
        """Gửi request chat và trả nội dung.

        Raise:
        - LLMTimeoutError: quá thời gian chờ.
        - LLMProviderError: lỗi 5xx / lỗi không xác định từ provider.
        - LLMUnavailableError: 401/402 (sai key, hết credit), lỗi kết nối.
        - RateLimitedError: 429 từ provider (service sẽ retry nếu còn lượt).
        - InvalidInputError: 400 từ provider (request sai - thường do tham số).
        """

    async def close(self) -> None:
        """Đóng tài nguyên HTTP nếu có."""

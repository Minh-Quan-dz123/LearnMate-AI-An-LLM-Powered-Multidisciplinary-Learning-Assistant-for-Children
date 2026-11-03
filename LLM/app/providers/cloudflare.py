
# ============================================================
# FILE: app/providers/cloudflare.py
# MỤC ĐÍCH: Adapter Cloudflare Workers AI tạo ảnh nền Module 3.
#
# - Nhận prompt từ BE thông qua LLM Server (tích hợp ở đợt sau).
# - Gọi model FLUX.1 Schnell bằng httpx.AsyncClient.
# - Kiểm tra Base64 và loại ảnh, trả dữ liệu nhất quán.
# - Chuyển lỗi HTTP thành exception có sẵn trong app/errors.py.
#
# LƯU Ý: Đây là provider tạo ẢNH, không kế thừa BaseProvider
# vì BaseProvider.chat() chỉ dành cho mô hình text/vision -> text.
# ============================================================

import base64
import binascii
import re
from dataclasses import dataclass

import httpx

from ..errors import (
    InvalidInputError,
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    RateLimitedError,
)


@dataclass(frozen=True)
class ImageProviderResult:
    """Ảnh Base64 (không có tiền tố data:), MIME, ID model và provider."""

    image_base64: str
    mime_type: str
    model: str
    provider: str = "cloudflare"


class CloudflareImageProvider:
    """Adapter sinh ảnh qua Cloudflare Workers AI REST API."""

    name = "cloudflare"

    # Giới hạn ảnh demo: tránh nhận ảnh bất thường quá lớn.
    MAX_IMAGE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        account_id: str,
        api_token: str,
        default_timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Tạo HTTP client; transport chỉ dùng để test bằng MockTransport."""
        if not account_id or not re.fullmatch(r"[A-Za-z0-9_-]+", account_id):
            raise LLMUnavailableError("CLOUDFLARE_ACCOUNT_ID chưa hợp lệ.")
        if not api_token or not api_token.strip():
            raise LLMUnavailableError("Chưa cấu hình CLOUDFLARE_API_TOKEN.")
        if default_timeout <= 0:
            raise InvalidInputError("Timeout Cloudflare phải lớn hơn 0.")

        self._account_id = account_id
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_token.strip()}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(default_timeout),
            transport=transport,
        )

    async def generate_image(
        self,
        model: str,
        prompt: str,
        steps: int = 4,
        timeout: float = 120.0,
    ) -> ImageProviderResult:
        """Sinh ảnh. Chỉ `prompt` và `steps` được gửi cho FLUX.1 Schnell.

        Ví dụ:
            result = await provider.generate_image(
                model="@cf/black-forest-labs/flux-1-schnell",
                prompt="A bright 2D cartoon classroom, no people",
            )
            # result.image_base64 -> BE sẽ giải mã và lưu Storage.
        """
        if not isinstance(model, str) or not re.fullmatch(
            r"@cf/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", model
        ):
            raise InvalidInputError("Model Cloudflare không hợp lệ.")
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 2048:
            raise InvalidInputError("Prompt ảnh phải dài từ 1 đến 2048 ký tự.")
        if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 8:
            raise InvalidInputError("Số bước tạo ảnh phải từ 1 đến 8.")
        if timeout <= 0:
            raise InvalidInputError("Timeout phải lớn hơn 0.")

        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self._account_id}/ai/run/{model}"
        )

        try:
            response = await self._client.post(
                url,
                json={"prompt": prompt.strip(), "steps": steps},
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("Cloudflare tạo ảnh quá lâu. Vui lòng thử lại.") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError("Không kết nối được Cloudflare Workers AI.") from exc

        if response.status_code != 200:
            self._raise_for_status(response.status_code)

        return self._parse_success(response, model)

    @classmethod
    def _parse_success(
        cls, response: httpx.Response, model: str
    ) -> ImageProviderResult:
        """Giải mã Base64 để kiểm tra MIME/giới hạn, nhưng trả Base64 cho BE."""
        try:
            body = response.json()
            if not isinstance(body, dict) or body.get("success") is False:
                raise ValueError("Cloudflare báo lỗi trong response.")

            # Workers AI REST trả envelope: {"success": true,
            # "result": {"image": "..."}}.
            result = body["result"]
            encoded = result["image"]
            if not isinstance(encoded, str) or not encoded:
                raise ValueError("Cloudflare không trả chuỗi Base64 ảnh.")

            # Kiểm tra dung lượng trước khi decode để tránh cấp phát quá lớn.
            if len(encoded) > (cls.MAX_IMAGE_BYTES + 2) * 4 // 3 + 4:
                raise ValueError("Ảnh vượt giới hạn 10 MB.")

            raw = base64.b64decode(encoded, validate=True)
            if not raw or len(raw) > cls.MAX_IMAGE_BYTES:
                raise ValueError("Ảnh rỗng hoặc vượt giới hạn 10 MB.")

            if raw.startswith(b"\xff\xd8\xff"):
                mime_type = "image/jpeg"
            elif raw.startswith(b"\x89PNG\r\n\x1a\n"):
                mime_type = "image/png"
            else:
                raise ValueError("Ảnh không phải JPEG hoặc PNG.")

            return ImageProviderResult(
                image_base64=encoded,
                mime_type=mime_type,
                model=model,
            )
        except (ValueError, TypeError, KeyError, binascii.Error) as exc:
            raise LLMProviderError(
                "Cloudflare trả ảnh không hợp lệ hoặc không đọc được."
            ) from exc

    @staticmethod
    def _raise_for_status(status: int) -> None:
        """Ánh xạ lỗi HTTP về exception chuẩn; không lộ API Token."""
        if status in (401, 402, 403):
            raise LLMUnavailableError(
                "Cloudflare từ chối truy cập. Kiểm tra Account ID, API Token và quota."
            )
        if status == 429:
            raise RateLimitedError("Cloudflare đang giới hạn lượt tạo ảnh.")
        if status in (400, 404, 422):
            raise InvalidInputError(
                "Yêu cầu tạo ảnh không hợp lệ. Kiểm tra model hoặc prompt.",
                details={"provider_status": status},
            )
        if status in (408, 504):
            raise LLMTimeoutError("Cloudflare tạo ảnh quá lâu. Vui lòng thử lại.")
        raise LLMProviderError(
            "Cloudflare gặp lỗi khi tạo ảnh. Vui lòng thử lại.",
            details={"provider_status": status},
        )

    async def close(self) -> None:
        """Giải phóng HTTP client khi server dừng."""
        await self._client.aclose()

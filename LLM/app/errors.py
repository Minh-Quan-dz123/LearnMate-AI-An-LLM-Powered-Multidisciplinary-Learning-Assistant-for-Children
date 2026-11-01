# ============================================================
# FILE: app/errors.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Định nghĩa exception chuẩn hóa và mã lỗi của LLM Server.
# Thông báo lỗi gửi ra cho người dùng cuối phải là tiếng Việt;
# BE sẽ chuyển tiếp nguyên văn các message này (hoặc tự diễn đạt lại).
#
# Mã lỗi thống nhất theo README mục 6.7:
# - INVALID_INPUT        -> 422
# - UNAUTHORIZED         -> 401
# - LLM_RATE_LIMITED     -> 429
# - LLM_UNAVAILABLE      -> 503
# - LLM_TIMEOUT          -> 504
# - LLM_PROVIDER_ERROR   -> 502 (lỗi phía nhà cung cấp model)
# ============================================================


class AppError(Exception):
    """Lỗi ứng dụng chuẩn hóa: kèm mã lỗi, HTTP status và thông báo tiếng Việt."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict | list | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class InvalidInputError(AppError):
    def __init__(self, message: str, details: dict | list | None = None) -> None:
        super().__init__("INVALID_INPUT", message, 422, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Khóa nội bộ không đúng hoặc bị thiếu.") -> None:
        super().__init__("UNAUTHORIZED", message, 401)


class RateLimitedError(AppError):
    def __init__(self, message: str = "Hệ thống đang quá tải. Vui lòng thử lại sau ít phút.") -> None:
        super().__init__("LLM_RATE_LIMITED", message, 429)


class LLMTimeoutError(AppError):
    def __init__(self, message: str = "Mô hình phản hồi quá lâu. Vui lòng thử lại.") -> None:
        super().__init__("LLM_TIMEOUT", message, 504)


class LLMUnavailableError(AppError):
    def __init__(self, message: str = "Hệ thống AI đang tạm thời gián đoạn. Vui lòng thử lại sau.") -> None:
        super().__init__("LLM_UNAVAILABLE", message, 503)


class LLMProviderError(AppError):
    """Lỗi trả về từ nhà cung cấp model (không phải lỗi đầu vào của BE)."""

    def __init__(
        self,
        message: str = "Mô hình gặp lỗi khi tạo nội dung. Vui lòng thử lại.",
        details: dict | list | None = None,
    ) -> None:
        super().__init__("LLM_PROVIDER_ERROR", message, 502, details)

# ============================================================
# FILE: app/config.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Đọc và quản lý cấu hình của LLM Server từ biến môi trường / .env.
# KHÔNG viết cứng API key, URL hay tên model vào mã nguồn.
# ============================================================

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình LLM Server đọc từ biến môi trường (hoặc file .env)."""

    # --------------------------------------------------------
    # 1. SERVER
    # --------------------------------------------------------
    app_name: str = "LearnMate AI - LLM Server"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8001

    # Môi trường hoạt động: development | production
    environment: str = "development"

    # Chế độ mock: true -> không gọi provider thật, trả nội dung mẫu.
    # Hữu ích để nhóm BE phát triển khi chưa có API key.
    mock_mode: bool = False

    # --------------------------------------------------------
    # 2. PROVIDER (NHÀ CUNG CẤP MODEL)
    # --------------------------------------------------------
    # openrouter | openai_compat | mock
    provider: str = "openrouter"

    # --- OpenRouter ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Tùy chọn nhưng được OpenRouter khuyến nghị:
    openrouter_site_url: str = "http://localhost:5173"
    openrouter_app_title: str = "LearnMate AI"

    # --- OpenAI-compatible (Ollama, vLLM, LM Studio...) ---
    openai_compat_base_url: str = "http://localhost:11434/v1"
    openai_compat_api_key: str = "ollama"

    # --------------------------------------------------------
    # 3. CẤU HÌNH MODEL (ÁNH XẠ NHÃN LOGIC -> MODEL THẬT)
    # --------------------------------------------------------
    # BE có thể gửi nhãn logic: "generation", "evaluation", "vision"
    # hoặc nhãn tiếng Việt trong contract. LLM Server ánh xạ sang model thật.
    model_generation: str = "openai/gpt-4o-mini"
    model_evaluation: str = "openai/gpt-4o-mini"
    model_vision: str = "openai/gpt-4o-mini"
    # Model dùng khi nhãn logic không xác định được:
    model_default: str = "openai/gpt-4o-mini"

    # Có cho phép BE gửi thẳng ID model của nhà cung cấp không?
    # false = chỉ chấp nhận nhãn logic (an toàn hơn, thống nhất model trong nhóm).
    allow_direct_model: bool = False

    # --------------------------------------------------------
    # 4. GIỚI HẠN GỌI MODEL
    # --------------------------------------------------------
    request_timeout_seconds: float = 60.0
    # Số lần thử lại tối đa SAU lần gọi đầu tiên (retry on timeout/429/5xx).
    max_retries: int = 2
    # Khoảng nghỉ cơ bản giữa các lần retry (nhân lũy thừa 2).
    retry_backoff_seconds: float = 1.0
    # Giới hạn số request mỗi phút cho toàn server (in-memory).
    rate_limit_requests_per_minute: int = 30
    # Giới hạn kích thước prompt (ký tự) để tránh lạm dụng tài nguyên.
    max_prompt_chars: int = 20000
    # Giới hạn an toàn cho max_output_tokens do BE gửi lên.
    max_output_tokens_limit: int = 4000

    # Giá trị mặc định nếu BE không gửi lên.
    default_temperature: float = 0.5
    default_max_output_tokens: int = 1800

    # --------------------------------------------------------
    # 5. BẢO MẬT NỘI BỘ (TÙY CHỌN)
    # --------------------------------------------------------
    # Nếu đặt giá trị, BE phải gửi kèm header: X-Internal-Api-Key: <giá trị>
    # Để trống = tắt kiểm tra (chỉ dùng cho môi trường demo nội bộ).
    internal_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --------------------------------------------------------
    # 6. ÁNH XẠ MODEL
    # --------------------------------------------------------
    def resolve_model(self, requested: str | None) -> str:
        """Ánh xạ nhãn logic (hoặc tên model) sang ID model thật.

        Thứ tự ưu tiên:
        1. Nhãn logic chuẩn: "generation" / "evaluation" / "vision" /
           các biến thể tiếng Việt thống nhất trong contract.
        2. Nếu allow_direct_model=true và BE gửi ID model -> dùng trực tiếp.
        3. Model mặc định.
        """
        if not requested:
            return self.model_default

        key = requested.strip().lower()

        alias_map = {
            "generation": self.model_generation,
            "sinh cau hoi": self.model_generation,
            "sinh câu hỏi": self.model_generation,
            "mô hình tạo nội dung mặc định": self.model_generation,
            "mo hinh tao noi dung mac dinh": self.model_generation,
            "evaluation": self.model_evaluation,
            "danh gia": self.model_evaluation,
            "đánh giá": self.model_evaluation,
            "mô hình đánh giá mặc định": self.model_evaluation,
            "mo hinh danh gia mac dinh": self.model_evaluation,
            "vision": self.model_vision,
            "anh": self.model_vision,
            "image": self.model_vision,
            "mô hình thị giác mặc định": self.model_vision,
        }

        if key in alias_map:
            return alias_map[key]

        if self.allow_direct_model:
            return requested.strip()

        return self.model_default


@lru_cache
def get_settings() -> Settings:
    """Trả về instance Settings dùng chung (tái sử dụng, đọc .env một lần)."""
    return Settings()

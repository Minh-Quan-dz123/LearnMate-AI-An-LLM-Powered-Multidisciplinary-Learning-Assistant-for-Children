# ============================================================
# FILE: app/schemas.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Pydantic schema cho request/response của LLM Server.
# Envelope response thống nhất:
#   { "success": bool, "message": str, "data": {...} | null,
#     "error": { "code": str, "details": ... } | null }
# ============================================================

from pydantic import BaseModel, Field
from typing import Literal


# ---------------------------------------------------------
# REQUEST: POST /internal/llm/generate
# ---------------------------------------------------------
class GenerateRequest(BaseModel):
    task: str = Field(
        default="Sinh nội dung",
        description="Tên tác vụ, dùng để log/trace. VD: 'Sinh câu hỏi trắc nghiệm'.",
        max_length=200,
    )
    model: str | None = Field(
        default=None,
        description=(
            "Nhãn logic của model: 'generation' | 'evaluation' | 'vision' "
            "hoặc biến thể tiếng Việt. Nếu để trống dùng model mặc định."
        ),
        max_length=200,
    )
    prompt: str = Field(..., description="Nội dung prompt do EGM phía BE xây dựng.")
    # Giới hạn temperature 0-2 là hằng số giao thức chat-completions (không phải cấu hình).
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    # Không đặt trần (le=...) ở đây: trần của max_output_tokens đọc từ .env
    # qua MAX_OUTPUT_TOKENS_LIMIT và được service áp dụng (clamp).
    # Nếu schema cũng chốt trần 4000 thì sửa .env sẽ không có tác dụng.
    max_output_tokens: int | None = Field(default=None, ge=1)
    # Tùy chọn: system_prompt nếu BE muốn tách system/data (không bắt buộc).
    system_prompt: str | None = Field(default=None, max_length=4000)


# ---------------------------------------------------------
# REQUEST: POST /internal/llm/vision (sau MVP)
# ---------------------------------------------------------
class VisionRequest(BaseModel):
    task: str = Field(default="Đánh giá hình ảnh", max_length=200)
    model: str | None = Field(default=None, max_length=200)
    prompt: str = Field(..., description="Prompt đánh giá tranh do EGM xây dựng.")
    # Ảnh dạng URL công khai HOẶC base64 (data URL).
    image_url: str | None = Field(
        default=None,
        description="URL ảnh (http/https) hoặc data URL base64, ví dụ data:image/png;base64,...",
    )
    # Hỗ trợ gửi base64 thuần + media type riêng nếu FE/BE không dùng data URL.
    image_base64: str | None = Field(default=None)
    image_media_type: str | None = Field(
        default=None, description="VD: image/png, image/jpeg."
    )
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    # Trần token lấy từ .env (MAX_OUTPUT_TOKENS_LIMIT), không hardcode ở schema.
    max_output_tokens: int | None = Field(default=None, ge=1)
    system_prompt: str | None = Field(default=None, max_length=4000)


# ---------------------------------------------------------
# DATA: nội dung trả về trong envelope
# ---------------------------------------------------------
class UsageInfo(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class GenerateData(BaseModel):
    content: str = Field(..., description="Nội dung text model tạo ra (thường là JSON string).")
    model: str = Field(..., description="ID model thực tế đã dùng.")
    provider: str = Field(..., description="Nhà cung cấp: openrouter | openai_compat | mock.")
    task: str | None = None
    usage: UsageInfo | None = None
    latency_ms: int | None = None
    attempts: int | None = Field(default=None, description="Số lần gọi provider đã thực hiện.")


class GenerateResponse(BaseModel):
    success: bool = True
    message: str = "Mô hình đã tạo nội dung"
    data: GenerateData
    error: dict | None = None


class VisionData(GenerateData):
    pass


class VisionResponse(BaseModel):
    success: bool = True
    message: str = "Mô hình đã phân tích hình ảnh"
    data: VisionData
    error: dict | None = None


# ---------------------------------------------------------
# ERROR envelope
# ---------------------------------------------------------
class ErrorBody(BaseModel):
    code: str
    details: dict | list | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: None = None
    error: ErrorBody


# ---------------------------------------------------------
# HEALTH / MODEL LIST
# ---------------------------------------------------------
class HealthData(BaseModel):
    status: str = "ok"
    provider: str
    mock_mode: bool
    version: str


class ModelInfo(BaseModel):
    logical_name: str
    real_model_id: str
    purpose: str


class ModelsData(BaseModel):
    models: list[ModelInfo]
    rate_limit_requests_per_minute: int
    request_timeout_seconds: float
    max_retries: int


class HealthResponse(BaseModel):
    success: bool = True
    message: str = "LLM Server đang hoạt động"
    data: HealthData
    error: dict | None = None


class ModelsResponse(BaseModel):
    success: bool = True
    message: str = "Danh sách model đang cấu hình"
    data: ModelsData
    error: dict | None = None



# ============================================================
# MODULE 3 - IMAGE GENERATION
# API: POST /internal/llm/image/generate
# ============================================================

class ImageGenerateRequest(BaseModel):
    """
    Request tạo hình nền hiện trường.

    BE gửi:
        task   : tên tác vụ
        model  : nhãn logic "image"
        prompt : mô tả hình ảnh
        steps  : số bước khuếch tán (tùy chọn)

    width/height được nhận theo API contract nhưng
    FLUX.1 Schnell trong adapter hiện tại chưa hỗ trợ
    ép kích thước ảnh bằng hai tham số này.
    """

    task: str = Field(
        default="detective_background",
        min_length=1,
        max_length=200,
    )

    model: str = Field(
        default="image",
        min_length=1,
        max_length=100,
    )

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2048,
    )

    steps: int | None = Field(
        default=None,
        ge=1,
        le=8,
    )

    width: int | None = Field(
        default=None,
        ge=1,
        le=2048,
        description="Kích thước mong muốn, chưa được adapter áp dụng.",
    )

    height: int | None = Field(
        default=None,
        ge=1,
        le=2048,
        description="Kích thước mong muốn, chưa được adapter áp dụng.",
    )


class ImageGenerateData(BaseModel):
    """
    Dữ liệu ảnh trả cho BE.

    image_base64:
        Chuỗi mã hóa ảnh PNG/JPEG.

    mime_type:
        image/png hoặc image/jpeg.

    model:
        ID model Cloudflare thực tế.

    provider:
        "cloudflare"
    """

    image_base64: str
    mime_type: str
    model: str
    provider: str
    task: str
    latency_ms: int

    # Thông báo giới hạn kích thước nếu có yêu cầu width/height.
    size_note: str | None = None


class ImageGenerateResponse(BaseModel):
    """Envelope thành công cho API tạo ảnh."""

    success: bool = True
    message: str = "Tạo ảnh thành công"
    data: ImageGenerateData
    error: dict | None = None



# ============================================================
# MODULE 3 — SPEECH API SCHEMAS
# ============================================================

class SpeechGenerateRequest(BaseModel):
    task: Literal[
        "detective_narration"
    ] = "detective_narration"

    model: Literal["tts"] = "tts"

    voice: Literal[
        "teacher_vi"
    ] = "teacher_vi"

    text: str = Field(
        min_length=1,
        max_length=2200,
    )


class SpeechGenerateData(BaseModel):
    audio_base64: str

    mime_type: Literal[
        "audio/wav"
    ] = "audio/wav"

    model: str

    provider: Literal[
        "gemini"
    ] = "gemini"

    voice: str


class SpeechGenerateResponse(BaseModel):
    success: bool = True

    message: str = "Đã tạo giọng đọc"

    data: SpeechGenerateData

    error: dict | None = None

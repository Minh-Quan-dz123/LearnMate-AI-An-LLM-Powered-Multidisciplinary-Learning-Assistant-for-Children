# ============================================================
# FILE: app/main.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# FastAPI app của LLM Server.
#
# Endpoint:
# - POST /internal/llm/generate   (MVP - text generation)
# - POST /internal/llm/vision     (sau MVP - đã dựng sẵn)
# - GET  /internal/llm/models     (xem model đang cấu hình)
# - GET  /health                  (kiểm tra server sống)
# - GET  /docs                    (Swagger UI)
# ============================================================

import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import Settings, get_settings

from .errors import (
    AppError,
    InvalidInputError,
    LLMUnavailableError,
    RateLimitedError,
    UnauthorizedError,
)

from .providers import (
    build_provider,
    build_detective_provider,
    build_image_provider,
)

from .rate_limit import SlidingWindowRateLimiter
from .schemas import (
    ErrorBody,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    HealthData,
    HealthResponse,
    ModelInfo,
    ModelsData,
    ModelsResponse,
    VisionRequest,
    VisionResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
    SpeechGenerateRequest,
    SpeechGenerateResponse,
)
from .service import GenerationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("llm-server")



# ============================================================
# LIFESPAN - KHỞI TẠO VÀ GIẢI PHÓNG CÁC PROVIDER
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời LLM Server.

    Khởi động:
        1. Khởi tạo provider cũ (Module 1-2).
        2. Khởi tạo GeminiProvider (Module 3).
        3. Khởi tạo CloudflareImageProvider (Module 3).
        4. Đưa các provider vào app.state.

    Tắt server:
        Đóng tất cả HTTP client để giải phóng kết nối.

    Nếu cấu hình Module 3 chưa đủ:
        Module 1-2 vẫn được khởi động bình thường.
        API tương ứng của Module 3 sẽ trả lỗi 503.
    """

    settings = get_settings()

    # --------------------------------------------------------
    # 1. PROVIDER CŨ - MODULE 1 VÀ MODULE 2
    # --------------------------------------------------------

    provider = build_provider(settings)

    # --------------------------------------------------------
    # 2. GEMINI - SINH KỊCH BẢN MODULE 3
    # --------------------------------------------------------

    detective_provider = None

    try:
        detective_provider = build_detective_provider(settings)

    except LLMUnavailableError as exc:
        logger.warning(
            "Gemini Module 3 chưa sẵn sàng: %s",
            exc.message,
        )

    # --------------------------------------------------------
    # 3. CLOUDFLARE - SINH ẢNH MODULE 3
    # --------------------------------------------------------

    image_provider = None

    try:
        image_provider = build_image_provider(settings)

    except LLMUnavailableError as exc:
        logger.warning(
            "Cloudflare Module 3 chưa sẵn sàng: %s",
            exc.message,
        )

    # --------------------------------------------------------
    # 4. LƯU CÁC THÀNH PHẦN VÀO APP.STATE
    # --------------------------------------------------------

    app.state.settings = settings

    # Provider mặc định vẫn là provider cũ.
    app.state.provider = provider

    # Provider chuyên tạo ảnh.
    app.state.image_provider = image_provider

    # Dispatcher đã viết ở đợt trước.
    app.state.service = GenerationService(
        settings,
        provider,
        detective_provider=detective_provider,
    )

    logger.info(
        "LLM Server started | provider=%s | mock_mode=%s",
        provider.name,
        settings.mock_mode,
    )

    logger.info(
        "Model map -> generation=%s | evaluation=%s | vision=%s",
        settings.model_generation,
        settings.model_evaluation,
        settings.model_vision,
    )

    logger.info(
        "Module 3 -> detective=%s | image=%s",
        settings.model_detective,
        settings.model_image,
    )

    try:
        # Từ đây FastAPI bắt đầu phục vụ request.
        yield

    finally:
        # ----------------------------------------------------
        # 5. ĐÓNG TẤT CẢ PROVIDER KHI SERVER DỪNG
        # ----------------------------------------------------

        # Tránh đóng trùng cùng một instance.
        closed: set[int] = set()

        for active in (
            image_provider,
            detective_provider,
            provider,
        ):
            if active is None:
                continue

            if id(active) in closed:
                continue

            closed.add(id(active))

            try:
                await active.close()

            except Exception:
                logger.exception(
                    "Không thể đóng provider: %s",
                    active.name,
                )

        logger.info("LLM Server stopped")



app = FastAPI(
    title="LearnMate AI - LLM Server",
    version="1.0.0",
    description=(
        "API nội bộ giữa Backend (EGM) và LLM Server. "
        "Nhận prompt từ BE, gọi model (OpenRouter), trả về response thống nhất."
    ),
    lifespan=lifespan,
)


# ============================================================
# ENVELOPE + EXCEPTION HANDLERS
# ============================================================
def success_envelope(message: str, data: dict) -> dict:
    return {"success": True, "message": message, "data": data, "error": None}


def error_envelope(code: str, message: str, details: dict | list | None = None) -> dict:
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": ErrorBody(code=code, details=details).model_dump(),
    }


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError %s on %s %s: %s", exc.code, request.method, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(exc.code, exc.message, exc.details),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_envelope(
            "INVALID_INPUT",
            "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại request.",
            details=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_envelope(
            "INTERNAL_ERROR",
            "Máy chủ AI gặp lỗi không xác định. Vui lòng thử lại sau.",
        ),
    )


# ============================================================
# AUTH NỘI BỘ (TÙY CHỌN)
# Nếu INTERNAL_API_KEY được đặt trong .env, mọi endpoint
# /internal/* phải gửi header X-Internal-Api-Key đúng giá trị.
# ============================================================
async def require_internal_key(
    request: Request,
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    settings: Settings = request.app.state.settings
    expected = settings.internal_api_key
    if not expected:
        # Chưa bật -> bỏ qua (môi trường demo nội bộ).
        return
    if x_internal_api_key != expected:
        raise UnauthorizedError()


# ============================================================
# ENDPOINT 1: HEALTH
# ============================================================
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health(request: Request) -> dict:
    settings: Settings = request.app.state.settings
    data = HealthData(
        status="ok",
        provider=request.app.state.provider.name,
        mock_mode=settings.mock_mode or settings.provider == "mock",
        version=settings.app_version,
    )
    return success_envelope("LLM Server đang hoạt động", data.model_dump())


# ============================================================
# ENDPOINT 2: MODEL LIST
# ============================================================
@app.get(
    "/internal/llm/models",
    response_model=ModelsResponse,
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)
async def list_models(request: Request) -> dict:
    settings: Settings = request.app.state.settings
    models = [
        ModelInfo(
            logical_name="generation",
            real_model_id=settings.model_generation,
            purpose="Sinh câu hỏi (Module 1 & 2)",
        ),
        ModelInfo(
            logical_name="evaluation",
            real_model_id=settings.model_evaluation,
            purpose="Đánh giá câu trả lời mở (Module 2)",
        ),
        ModelInfo(
            logical_name="vision",
            real_model_id=settings.model_vision,
            purpose="Đánh giá bài vẽ (Module 3, sau MVP)",
        ),
    ]

    
    if (
        settings.provider_tts == "gemini"
        and settings.model_tts
    ):
        models.append(
            ModelInfo(
                logical_name="tts",
                real_model_id=settings.model_tts,
                purpose=(
                    "Giọng cô giáo Module 3 "
                    "(Gemini TTS)"
                ),
            )
        )


    data = ModelsData(
        models=models,
        rate_limit_requests_per_minute=settings.rate_limit_requests_per_minute,
        request_timeout_seconds=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
    )
    return success_envelope("Danh sách model đang cấu hình", data.model_dump())


# ============================================================
# ENDPOINT 3: TEXT GENERATION (MVP)
# ============================================================
@app.post(
    "/internal/llm/generate",
    response_model=GenerateResponse,
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)
async def generate(body: GenerateRequest, request: Request) -> dict:
    service: GenerationService = request.app.state.service

    logger.info("Generate request | task=%s | model=%s", body.task, body.model)

    data = await service.generate(
        prompt=body.prompt,
        model=body.model,
        task=body.task,
        temperature=body.temperature,
        max_output_tokens=body.max_output_tokens,
        system_prompt=body.system_prompt,
    )

    return success_envelope("Mô hình đã tạo nội dung", data)


# ============================================================
# ENDPOINT 4: VISION (SAU MVP - đã dựng sẵn)
# ============================================================
@app.post(
    "/internal/llm/vision",
    response_model=VisionResponse,
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)
async def vision(body: VisionRequest, request: Request) -> dict:
    service: GenerationService = request.app.state.service

    logger.info("Vision request | task=%s | model=%s", body.task, body.model)

    data = await service.generate_vision(
        prompt=body.prompt,
        image_url=body.image_url,
        image_base64=body.image_base64,
        image_media_type=body.image_media_type,
        model=body.model,
        task=body.task,
        temperature=body.temperature,
        max_output_tokens=body.max_output_tokens,
        system_prompt=body.system_prompt,
    )

    return success_envelope("Mô hình đã phân tích hình ảnh", data)



# ============================================================
# ENDPOINT 5 - IMAGE GENERATION (MODULE 3)
# POST /internal/llm/image/generate
# ============================================================

@app.post(
    "/internal/llm/image/generate",
    response_model=ImageGenerateResponse,
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)
async def generate_image(
    body: ImageGenerateRequest,
    request: Request,
) -> dict:
    """
    Sinh hình nền cho trò chơi Thám tử khoa học.

    Luồng:
        BE
         |
         v
        FastAPI endpoint
         |
         v
        Kiểm tra model + provider + rate limit
         |
         v
        CloudflareImageProvider.generate_image()
         |
         v
        Cloudflare Workers AI
         |
         v
        ImageProviderResult
         |
         v
        Response envelope -> BE

    Endpoint này không lưu file ảnh.
    BE chịu trách nhiệm lưu ảnh lên Supabase Storage.
    """

    # --------------------------------------------------------
    # 1. KIỂM TRA NHÃN MODEL
    # --------------------------------------------------------

    # Chỉ chấp nhận nhãn logic "image".
    # Không tự fallback về model text mặc định.
    if body.model.strip().lower() != "image":
        raise InvalidInputError(
            "Model tạo ảnh phải dùng nhãn 'image'."
        )

    # --------------------------------------------------------
    # 2. LẤY SETTINGS VÀ PROVIDER
    # --------------------------------------------------------

    settings: Settings = request.app.state.settings

    image_provider = request.app.state.image_provider

    if image_provider is None:
        raise LLMUnavailableError(
            "Cloudflare chưa được cấu hình, "
            "hoặc MOCK_MODE đang bật."
        )

    # Model thực tế được cấu hình trong .env.
    model_id = settings.model_image.strip()

    if not model_id:
        raise LLMUnavailableError(
            "Thiếu MODEL_IMAGE trong cấu hình."
        )

    # --------------------------------------------------------
    # 3. KIỂM TRA RATE LIMIT
    # --------------------------------------------------------

    # Dùng chung rate limiter với text service.
    service: GenerationService = request.app.state.service

    if not service.rate_limiter.check():
        raise RateLimitedError()

    # --------------------------------------------------------
    # 4. XÁC ĐỊNH SỐ BƯỚC TẠO ẢNH
    # --------------------------------------------------------

    # Ưu tiên steps từ request.
    # Nếu BE không truyền thì sử dụng .env.
    steps = (
        body.steps
        if body.steps is not None
        else settings.image_generation_steps
    )

    # --------------------------------------------------------
    # 5. GỌI CLOUDFLARE
    # --------------------------------------------------------

    started = time.monotonic()

    result = await image_provider.generate_image(
        model=model_id,
        prompt=body.prompt,
        steps=steps,
        timeout=settings.image_timeout_seconds,
    )

    elapsed_ms = int(
        (time.monotonic() - started) * 1000
    )

    # --------------------------------------------------------
    # 6. THÔNG BÁO GIỚI HẠN KÍCH THƯỚC
    # --------------------------------------------------------

    # Adapter FLUX.1 Schnell hiện chỉ gửi prompt/steps.
    # width/height không được gửi sang Cloudflare.
    size_note = None

    if body.width is not None or body.height is not None:
        size_note = (
            "Model hiện chưa hỗ trợ ép kích thước ảnh; "
            "width/height chỉ là thông tin yêu cầu và "
            "không được gửi đến Cloudflare."
        )

    # --------------------------------------------------------
    # 7. TRẢ KẾT QUẢ CHUẨN CHO BE
    # --------------------------------------------------------

    data = {
        "image_base64": result.image_base64,
        "mime_type": result.mime_type,
        "model": result.model,
        "provider": result.provider,
        "task": body.task,
        "latency_ms": elapsed_ms,
        "size_note": size_note,
    }

    return success_envelope(
        "Tạo ảnh thành công",
        data,
    )



# ============================================================
# MODULE 3 — GEMINI TTS
# POST /internal/llm/speech/generate
# ============================================================

@app.post(
    "/internal/llm/speech/generate",
    response_model=SpeechGenerateResponse,
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)
async def generate_speech_endpoint(
    body: SpeechGenerateRequest,
    request: Request,
) -> dict:
    from base64 import b64encode

    from .providers.gemini_speech import (
        generate_speech,
        MAX_AUDIO_BYTES,
    )

    settings: Settings = request.app.state.settings

    if (
        settings.provider_tts != "gemini"
        or not settings.model_tts
    ):
        raise LLMUnavailableError(
            "Chưa bật Gemini TTS trong LLM Server."
        )

    if not (
        request.app.state.service
        .rate_limiter.check()
    ):
        raise RateLimitedError()

    wav = await generate_speech(
        base_url=settings.gemini_base_url,
        api_key=settings.gemini_api_key,
        model=settings.model_tts,
        voice=settings.tts_voice_name,
        text=body.text,
        timeout=settings.tts_timeout_seconds,
    )

    if (
        len(wav) > MAX_AUDIO_BYTES
        or not wav.startswith(b"RIFF")
        or wav[8:12] != b"WAVE"
    ):
        raise LLMUnavailableError(
            "Âm thanh Gemini TTS "
            "không đúng định dạng WAV."
        )

    return success_envelope(
        "Đã tạo giọng đọc",
        {
            "audio_base64":
                b64encode(wav).decode("ascii"),
            "mime_type": "audio/wav",
            "model": settings.model_tts,
            "provider": "gemini",
            "voice": settings.tts_voice_name,
        },
    )



# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=_settings.host,
        port=_settings.port,
        reload=(_settings.environment == "development"),
    )

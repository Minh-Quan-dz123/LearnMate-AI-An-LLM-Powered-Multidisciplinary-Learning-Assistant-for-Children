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
from .errors import AppError, UnauthorizedError
from .providers import build_provider
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
)
from .service import GenerationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("llm-server")


# ============================================================
# LIFESPAN: khởi tạo provider + service dùng chung
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    provider = build_provider(settings)
    app.state.settings = settings
    app.state.provider = provider
    app.state.service = GenerationService(settings, provider)

    logger.info("LLM Server started | provider=%s | mock_mode=%s", provider.name, settings.mock_mode)
    logger.info(
        "Model map -> generation=%s | evaluation=%s | vision=%s",
        settings.model_generation,
        settings.model_evaluation,
        settings.model_vision,
    )
    try:
        yield
    finally:
        await provider.close()
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

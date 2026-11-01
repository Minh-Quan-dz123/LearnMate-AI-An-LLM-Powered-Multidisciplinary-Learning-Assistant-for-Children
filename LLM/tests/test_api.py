# ============================================================
# FILE: tests/test_api.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Test tự động cho LLM Server ở chế độ MOCK (không tốn credit).
#
# Chạy: pytest -v  (trong thư mục LLM)
# ============================================================

import os

# Đặt biến môi trường TRƯỚC khi import app (chế độ mock).
os.environ["MOCK_MODE"] = "true"
os.environ["PROVIDER"] = "mock"
os.environ["MODEL_GENERATION"] = "openai/gpt-4o-mini"
os.environ["RATE_LIMIT_REQUESTS_PER_MINUTE"] = "100"
os.environ["INTERNAL_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

# Xóa cache settings để đọc lại env vừa set.
get_settings.cache_clear()

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. HEALTH
# ---------------------------------------------------------
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["mock_mode"] is True


# ---------------------------------------------------------
# 2. MODEL LIST
# ---------------------------------------------------------
def test_model_list(client):
    response = client.get("/internal/llm/models")
    assert response.status_code == 200
    body = response.json()
    logical_names = [m["logical_name"] for m in body["data"]["models"]]
    assert logical_names == ["generation", "evaluation", "vision"]


# ---------------------------------------------------------
# 3. GENERATE – THÀNH CÔNG
# ---------------------------------------------------------
def test_generate_success(client):
    payload = {
        "task": "Sinh câu hỏi trắc nghiệm",
        "model": "generation",
        "prompt": "Tạo 1 câu hỏi trắc nghiệm về động vật. Trả về JSON.",
        "temperature": 0.5,
        "max_output_tokens": 800,
    }
    response = client.post("/internal/llm/generate", json=payload)
    assert response.status_code == 200
    body = response.json()

    # Envelope thống nhất.
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "Mô hình đã tạo nội dung"

    data = body["data"]
    assert isinstance(data["content"], str) and len(data["content"]) > 0
    assert data["model"] == "openai/gpt-4o-mini"  # đã ánh xạ nhãn logic
    assert data["provider"] == "mock"
    assert data["attempts"] >= 1
    assert isinstance(data["latency_ms"], int)


def test_generate_content_is_valid_json_when_prompt_asks(client):
    payload = {
        "task": "test",
        "prompt": "Tạo câu hỏi. Trả về JSON hợp lệ.",
    }
    response = client.post("/internal/llm/generate", json=payload)
    data = response.json()["data"]

    # Nội dung mock là JSON hợp lệ để EGM parse được.
    import json

    parsed = json.loads(data["content"])
    assert "questions" in parsed


# ---------------------------------------------------------
# 4. GENERATE – LỖI ĐẦU VÀO
# ---------------------------------------------------------
def test_generate_empty_prompt(client):
    response = client.post(
        "/internal/llm/generate", json={"task": "test", "prompt": "   "}
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_INPUT"
    # Thông báo lỗi phải là tiếng Việt, không rỗng.
    assert len(body["message"]) > 0


def test_generate_prompt_too_long(client):
    long_prompt = "a" * 30000  # vượt MAX_PROMPT_CHARS mặc định 20000
    response = client.post(
        "/internal/llm/generate", json={"task": "test", "prompt": long_prompt}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_generate_missing_prompt_field(client):
    response = client.post("/internal/llm/generate", json={"task": "test"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_generate_temperature_out_of_range(client):
    response = client.post(
        "/internal/llm/generate",
        json={"task": "test", "prompt": "hỏi", "temperature": 9.0},
    )
    assert response.status_code == 422


# ---------------------------------------------------------
# 5. ÁNH XẠ MODEL
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "logical,expected",
    [
        ("generation", "openai/gpt-4o-mini"),
        ("evaluation", "openai/gpt-4o-mini"),
        ("vision", "openai/gpt-4o-mini"),
        ("Mô hình tạo nội dung mặc định", "openai/gpt-4o-mini"),
        (None, "openai/gpt-4o-mini"),  # MODEL_DEFAULT
        ("unknown-label", "openai/gpt-4o-mini"),  # rơi về default khi ALLOW_DIRECT_MODEL=false
    ],
)
def test_model_alias_resolution(client, logical, expected):
    response = client.post(
        "/internal/llm/generate",
        json={"task": "test", "prompt": "xin chào", "model": logical},
    )
    assert response.status_code == 200
    assert response.json()["data"]["model"] == expected


# ---------------------------------------------------------
# 6. VISION
# ---------------------------------------------------------
def test_vision_success_with_base64(client):
    payload = {
        "task": "Đánh giá bài vẽ",
        "model": "vision",
        "prompt": "Bạn đang xem bức tranh do trẻ vẽ. Trả về JSON.",
        "image_base64": "aGVsbG8=",  # "hello" giả lập
        "image_media_type": "image/png",
    }
    response = client.post("/internal/llm/vision", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["content"]


def test_vision_success_with_data_url(client):
    payload = {
        "prompt": "Đánh giá tranh",
        "image_url": "data:image/png;base64,aGVsbG8=",
    }
    response = client.post("/internal/llm/vision", json=payload)
    assert response.status_code == 200


def test_vision_missing_image(client):
    response = client.post(
        "/internal/llm/vision", json={"prompt": "Đánh giá tranh"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_vision_invalid_image_url(client):
    response = client.post(
        "/internal/llm/vision",
        json={"prompt": "Đánh giá tranh", "image_url": "ftp://sai-protocol"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------
# 7. RATE LIMIT
# ---------------------------------------------------------
def test_rate_limit(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "2")
    monkeypatch.setenv("MOCK_MODE", "true")

    # Tạo app tạm với giới hạn thấp (TestClient mới đọc lại settings).
    from app.config import Settings
    from app.providers import MockProvider
    from app.rate_limit import SlidingWindowRateLimiter
    from app.service import GenerationService

    settings = Settings()
    assert settings.rate_limit_requests_per_minute == 2

    limiter = SlidingWindowRateLimiter(max_requests=2)
    assert limiter.check() is True
    assert limiter.check() is True
    assert limiter.check() is False  # vượt giới hạn

    # Service dùng chung rate limiter.
    service = GenerationService(settings, MockProvider())
    import asyncio

    async def run():
        ok = 0
        for _ in range(5):
            try:
                await service.generate(prompt="xin chào")
                ok += 1
            except Exception as exc:
                from app.errors import RateLimitedError

                assert isinstance(exc, RateLimitedError)
        return ok

    assert asyncio.run(run()) == 2

    get_settings.cache_clear()


# ---------------------------------------------------------
# 8. AUTH NỘI BỘ
# ---------------------------------------------------------
def test_internal_auth_required(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("INTERNAL_API_KEY", "secret-test-key")
    monkeypatch.setenv("MOCK_MODE", "true")

    with TestClient(app) as c:
        # Không có key -> 401
        response = c.get("/internal/llm/models")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

        # Sai key -> 401
        response = c.get(
            "/internal/llm/models",
            headers={"X-Internal-Api-Key": "sai-key"},
        )
        assert response.status_code == 401

        # Đúng key -> 200
        response = c.get(
            "/internal/llm/models",
            headers={"X-Internal-Api-Key": "secret-test-key"},
        )
        assert response.status_code == 200

        # /health KHÔNG yêu cầu key (dành cho monitoring).
        assert c.get("/health").status_code == 200

    monkeypatch.delenv("INTERNAL_API_KEY")
    get_settings.cache_clear()

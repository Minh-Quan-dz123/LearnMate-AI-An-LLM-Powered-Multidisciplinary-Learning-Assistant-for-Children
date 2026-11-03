
# ============================================================
# FILE: tests/test_image_api.py
#
# Unit test API tạo ảnh Module 3.
#
# Không gọi Cloudflare thật.
# Không sử dụng API Token thật.
# Không tiêu tốn quota.
# ============================================================

import base64

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.providers.cloudflare import ImageProviderResult


MODEL_ID = "@cf/black-forest-labs/flux-1-schnell"


# ============================================================
# 1. PROVIDER GIẢ
# ============================================================

class FakeImageProvider:
    """
    Mô phỏng CloudflareImageProvider.

    Lưu tham số gọi vào self.calls để kiểm tra
    endpoint có truyền đúng model, prompt, steps không.
    """

    name = "cloudflare"

    def __init__(self):
        self.calls = []

    async def generate_image(
        self,
        model,
        prompt,
        steps,
        timeout,
    ):
        self.calls.append({
            "model": model,
            "prompt": prompt,
            "steps": steps,
            "timeout": timeout,
        })

        # Dữ liệu ảnh JPEG giả để kiểm tra contract.
        fake_image = b"\xff\xd8\xffdemo"

        return ImageProviderResult(
            image_base64=base64.b64encode(
                fake_image
            ).decode("ascii"),
            mime_type="image/jpeg",
            model=model,
        )


# ============================================================
# 2. FIXTURE FASTAPI TEST CLIENT
# ============================================================

@pytest.fixture
def client(monkeypatch):
    """
    Tạo FastAPI TestClient trong MOCK_MODE.

    Sau khi ứng dụng khởi động, thay image_provider
    bằng FakeImageProvider để test riêng endpoint.

    Không sửa .env của người dùng.
    """

    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("PROVIDER", "mock")

    monkeypatch.setenv(
        "MODEL_GENERATION", "test/generation"
    )
    monkeypatch.setenv(
        "MODEL_EVALUATION", "test/evaluation"
    )
    monkeypatch.setenv(
        "MODEL_VISION", "test/vision"
    )
    monkeypatch.setenv(
        "MODEL_DEFAULT", "test/default"
    )
    monkeypatch.setenv(
        "MODEL_IMAGE", MODEL_ID
    )

    monkeypatch.setenv(
        "INTERNAL_API_KEY", "unit-test-secret"
    )
    monkeypatch.setenv(
        "RATE_LIMIT_REQUESTS_PER_MINUTE", "100"
    )

    get_settings.cache_clear()

    try:
        with TestClient(app) as c:
            # Chỉ thay provider tạo ảnh trong môi trường test.
            c.app.state.image_provider = FakeImageProvider()
            yield c

    finally:
        get_settings.cache_clear()


def auth():
    """Header xác thực nội bộ dùng riêng cho test."""
    return {
        "X-Internal-Api-Key": "unit-test-secret"
    }


# ============================================================
# TEST 1 - TẠO ẢNH THÀNH CÔNG
# ============================================================

def test_image_generate_success(client):
    payload = {
        "task": "detective_background",
        "model": "image",
        "prompt": "A sunny cartoon garden",
        "steps": 4,
        "width": 1024,
        "height": 576,
    }

    response = client.post(
        "/internal/llm/image/generate",
        json=payload,
        headers=auth(),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["success"] is True
    assert body["error"] is None

    data = body["data"]

    assert data["provider"] == "cloudflare"
    assert data["model"] == MODEL_ID
    assert data["mime_type"] == "image/jpeg"

    assert base64.b64decode(
        data["image_base64"]
    ).startswith(b"\xff\xd8\xff")

    # width/height chưa được model áp dụng.
    assert data["size_note"] is not None

    # Endpoint phải truyền đúng steps cho provider.
    calls = client.app.state.image_provider.calls
    assert len(calls) == 1
    assert calls[0]["steps"] == 4


# ============================================================
# TEST 2 - THIẾU INTERNAL API KEY
# ============================================================

def test_internal_key_required(client):
    response = client.post(
        "/internal/llm/image/generate",
        json={"prompt": "A garden"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


# ============================================================
# TEST 3 - NHÃN MODEL KHÔNG HỢP LỆ
# ============================================================

def test_wrong_model_rejected(client):
    response = client.post(
        "/internal/llm/image/generate",
        json={
            "model": "generation",
            "prompt": "A garden",
        },
        headers=auth(),
    )

    assert response.status_code == 422

    # Không được gọi provider khi model sai.
    assert client.app.state.image_provider.calls == []


# ============================================================
# TEST 4 - THIẾU PROMPT
# ============================================================

def test_missing_prompt_rejected(client):
    response = client.post(
        "/internal/llm/image/generate",
        json={},
        headers=auth(),
    )

    assert response.status_code == 422


# ============================================================
# TEST 5 - STEPS KHÔNG HỢP LỆ
# ============================================================

def test_invalid_steps_rejected(client):
    response = client.post(
        "/internal/llm/image/generate",
        json={
            "prompt": "A garden",
            "steps": 9,
        },
        headers=auth(),
    )

    assert response.status_code == 422


# ============================================================
# TEST 6 - PROVIDER KHÔNG KHẢ DỤNG
# ============================================================

def test_image_provider_unavailable(client):
    # Giả lập chưa cấu hình Cloudflare.
    client.app.state.image_provider = None

    response = client.post(
        "/internal/llm/image/generate",
        json={"prompt": "A garden"},
        headers=auth(),
    )

    assert response.status_code == 503
    assert (
        response.json()["error"]["code"]
        == "LLM_UNAVAILABLE"
    )

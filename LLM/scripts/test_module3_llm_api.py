
# ============================================================
# FILE: LLM/scripts/test_module3_llm_api.py
#
# MỤC ĐÍCH:
# Kiểm thử tích hợp THẬT qua LLM Server :8001.
#
# 1. Kiểm tra LLM Server đang hoạt động.
# 2. Gọi Gemini qua /internal/llm/generate.
# 3. Kiểm tra JSON bằng Pydantic.
# 4. Gọi Cloudflare qua /internal/llm/image/generate.
# 5. Giải mã và lưu ảnh PNG/JPEG.
#
# Không cần chạy BE hoặc FE.
# Có sử dụng API quota thật của Gemini và Cloudflare.
# ============================================================

import base64
import binascii
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

# Tái sử dụng những thành phần đã kiểm thử trong PoC.
from test_detective_gemini import DetectiveCase, build_prompt
from test_detective_cloudflare import (
    SCENE_DESCRIPTIONS,
    ASSET_DESCRIPTIONS,
)

# ============================================================
# 1. CẤU HÌNH
# ============================================================

# LLM/scripts/ -> LLM/ -> project_LLM/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

load_dotenv(PROJECT_ROOT / ".env")

SERVER_URL = os.getenv(
    "LLM_SERVER_URL",
    "http://127.0.0.1:8001",
).rstrip("/")

# Khóa xác thực NỘI BỘ giữa BE và LLM Server.
# Không phải GEMINI_API_KEY hay CLOUDFLARE_API_TOKEN.
INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY", ""
).strip()

HEADERS = (
    {"X-Internal-Api-Key": INTERNAL_API_KEY}
    if INTERNAL_API_KEY
    else {}
)


# ============================================================
# 2. HÀM GỌI HTTP API CHUNG
# ============================================================

def call_api(
    client: httpx.Client,
    method: str,
    path: str,
    **kwargs,
) -> dict:
    """
    Gọi API của LLM Server.

    Kiểm tra:
        - HTTP status có thành công không?
        - Response có phải JSON không?
        - success có bằng True không?
        - data có phải object không?

    Không in API key hoặc token ra terminal.
    """

    response = client.request(
        method,
        f"{SERVER_URL}{path}",
        headers=HEADERS,
        **kwargs,
    )

    try:
        body = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"{path}: server không trả JSON "
            f"(HTTP {response.status_code})."
        ) from exc

    if not isinstance(body, dict):
        raise RuntimeError(
            f"{path}: response JSON không phải object."
        )

    if (
        response.status_code != 200
        or body.get("success") is not True
    ):
        error = body.get("error") or {}

        raise RuntimeError(
            f"{path}: HTTP {response.status_code}, "
            f"code={error.get('code', 'UNKNOWN')}, "
            f"message={body.get('message', 'Không có thông báo')}."
        )

    if not isinstance(body.get("data"), dict):
        raise RuntimeError(
            f"{path}: response thiếu data object."
        )

    return body["data"]


# ============================================================
# 3. HÀM TẠO PROMPT ẢNH TỪ KỊCH BẢN ĐÃ VALIDATE
# ============================================================

def build_background_prompt(case: DetectiveCase) -> str:
    """
    Tạo prompt hình nền dựa trên:
        - scene_id: hiện trường đã chọn.
        - objects: vật thể tương tác cần tránh vẽ trùng.

    Ảnh chỉ là background.
    Các vật thể tương tác sẽ do FE chồng sprite lên.
    """

    scene = SCENE_DESCRIPTIONS.get(case.scene_id)

    if not scene:
        raise ValueError(
            f"Chưa hỗ trợ scene_id={case.scene_id}."
        )

    asset_names = []

    for obj in case.objects:
        asset = ASSET_DESCRIPTIONS.get(obj.asset_id)

        if not asset:
            raise ValueError(
                f"Chưa hỗ trợ asset_id={obj.asset_id}."
            )

        asset_names.append(asset)

    forbidden = ", ".join(sorted(set(asset_names)))

    return (
        "A cheerful 2D cartoon point-and-click educational "
        f"detective game background for children: {scene}. "
        "Bright friendly colors, clean shapes, "
        "wide 16:9 composition. "
        "Environment only, leave open spaces for overlay sprites. "
        "No text, no people, no logos, no frightening elements. "
        f"Do not draw these interactive objects: {forbidden}."
    )


# ============================================================
# 4. LUỒNG KIỂM THỬ TÍCH HỢP
# ============================================================

def run() -> None:

    # --------------------------------------------------------
    # BƯỚC 1: KIỂM TRA SERVER
    # --------------------------------------------------------

    print(f"[1/4] Kiểm tra LLM Server: {SERVER_URL}")

    with httpx.Client(timeout=180.0) as client:

        health = call_api(
            client,
            "GET",
            "/health",
        )

        if health.get("status") != "ok":
            raise RuntimeError(
                "Health check không trả status=ok."
            )

        print("[PASS] Server đang hoạt động.")

        if health.get("mock_mode"):
            print(
                "[LƯU Ý] Provider mặc định đang mock; "
                "các bước sau sẽ xác minh provider "
                "Gemini/Cloudflare thật."
            )

        # ----------------------------------------------------
        # BƯỚC 2: GỌI GEMINI QUA LLM SERVER
        # ----------------------------------------------------

        print(
            "[2/4] Gọi Gemini qua "
            "/internal/llm/generate..."
        )

        text_data = call_api(
            client,
            "POST",
            "/internal/llm/generate",
            json={
                "task": "detective_case_generation",
                "model": "detective",
                "prompt": build_prompt(),
                "temperature": 0.6,
                "max_output_tokens": 4000,
            },
        )

        # Bắt buộc provider phải thực sự là Gemini.
        if text_data.get("provider") != "gemini":
            raise RuntimeError(
                f"Sai provider: "
                f"{text_data.get('provider')!r}, "
                "cần 'gemini'."
            )

        content = text_data.get("content")

        if not isinstance(content, str):
            raise RuntimeError(
                "Gemini response thiếu data.content dạng chuỗi."
            )

        # Kiểm tra JSON và các ràng buộc game engine.
        case = DetectiveCase.model_validate_json(content)

        # Lưu JSON để kiểm tra thủ công.
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        json_file = (
            OUTPUT_DIR / "detective_case_via_server.json"
        )

        json_file.write_text(
            json.dumps(
                case.model_dump(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[PASS] {case.title} | "
            f"{len(case.objects)} objects | "
            f"{len(case.clues)} clues"
        )

        print(
            f"       provider={text_data.get('provider')} "
            f"| model={text_data.get('model')}"
        )

        print(f"       JSON: {json_file}")

        # ----------------------------------------------------
        # BƯỚC 3: GỌI CLOUDFLARE QUA LLM SERVER
        # ----------------------------------------------------

        print(
            "[3/4] Gọi Cloudflare qua "
            "/internal/llm/image/generate..."
        )

        image_data = call_api(
            client,
            "POST",
            "/internal/llm/image/generate",
            json={
                "task": "detective_background",
                "model": "image",
                "prompt": build_background_prompt(case),
                "steps": 4,
            },
        )

        if image_data.get("provider") != "cloudflare":
            raise RuntimeError(
                "API ảnh không sử dụng Cloudflare."
            )

        encoded = image_data.get("image_base64")

        if not isinstance(encoded, str):
            raise RuntimeError(
                "API ảnh không trả image_base64 dạng chuỗi."
            )

        # Tránh xử lý dữ liệu Base64 quá lớn.
        if len(encoded) > 14_000_000:
            raise RuntimeError(
                "Ảnh Base64 lớn bất thường."
            )

        # Chuyển Base64 -> bytes.
        raw = base64.b64decode(
            encoded,
            validate=True,
        )

        # Kiểm tra MIME và chữ ký thực tế của ảnh.
        mime = image_data.get("mime_type")

        if (
            mime == "image/png"
            and raw.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            ext = ".png"

        elif (
            mime == "image/jpeg"
            and raw.startswith(b"\xff\xd8\xff")
        ):
            ext = ".jpg"

        else:
            raise RuntimeError(
                "MIME không khớp chữ ký PNG/JPEG trong ảnh."
            )

        # Lưu hình nền vào output.
        image_file = (
            OUTPUT_DIR
            / f"detective_background_via_server{ext}"
        )

        image_file.write_bytes(raw)

        print(
            f"[PASS] provider=cloudflare | "
            f"kích thước dữ liệu={len(raw):,} bytes"
        )

        print(f"       Ảnh: {image_file}")

    # --------------------------------------------------------
    # BƯỚC 4: HOÀN THÀNH
    # --------------------------------------------------------

    print(
        "[4/4] HOÀN THÀNH: "
        "2 API thật của Module 3 hoạt động "
        "qua LLM Server :8001."
    )

    print(
        "Hãy mở JSON và ảnh để kiểm tra chất lượng "
        "nội dung trước khi sang BE."
    )


# ============================================================
# 5. CHẠY CHƯƠNG TRÌNH
# ============================================================

if __name__ == "__main__":
    try:
        run()

    except (
        httpx.RequestError,
        RuntimeError,
        ValueError,
        ValidationError,
        binascii.Error,
    ) as exc:
        print(f"[FAIL] {exc}")
        sys.exit(1)

# Script này sử dụng kịch bản JSON đã sinh ở Script 1 để 
# tạo prompt ảnh theo đúng hiện trường và những vật thể 
# tương tác cần tránh. Sau đó gọi Cloudflare, giải mã 
# Base64 và lưu hình ảnh vào máy.


"""Thử Cloudflare tạo ảnh nền từ JSON vụ án do Gemini sinh."""

import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CASE_FILE = OUTPUT_DIR / "detective_case.json"

# Mô tả từng hiện trường bằng tiếng Anh.
SCENE_DESCRIPTIONS = {
    "classroom": (
        "a bright elementary school classroom "
        "with desks, windows, shelves"
    ),
    "garden": (
        "a peaceful school garden with "
        "a fence and open soil patches"
    ),
    "lab": (
        "a cheerful safe science classroom "
        "laboratory with tables and cabinets"
    ),
}

# Dùng để yêu cầu AI không vẽ trùng các sprite tương tác.
ASSET_DESCRIPTIONS = {
    "wilted_plant": "wilted potted plants",
    "dry_soil": "dry soil samples",
    "watering_can": "watering cans",
    "notebook": "notebooks",
    "water_tank": "water tanks",
    "lamp": "desk lamps",
    "thermometer": "thermometers",
    "toy_robot": "toy robots",
    "magnifier": "magnifying glasses",
}


def main() -> int:
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    model = os.getenv(
        "MODEL_IMAGE",
        "@cf/black-forest-labs/flux-1-schnell",
    )

    if not account_id or not api_token:
        print("THIẾU CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN")
        return 1

    if not CASE_FILE.exists():
        print("Chưa có detective_case.json. Hãy chạy Gemini trước.")
        return 1

    # Đọc kịch bản đã được kiểm tra ở Script 1.
    case = json.loads(CASE_FILE.read_text(encoding="utf-8"))

    scene = SCENE_DESCRIPTIONS.get(case["scene_id"])

    if scene is None:
        print(f"Scene chưa được hỗ trợ: {case['scene_id']}")
        return 1

    # Tìm những vật thể tương tác không nên xuất hiện trên nền.
    forbidden = ", ".join(sorted({
        ASSET_DESCRIPTIONS[obj["asset_id"]]
        for obj in case["objects"]
    }))

    # Tạo prompt hình nền.
    prompt = (
        "A cheerful 2D cartoon point-and-click science "
        f"detective game background: {scene}. "
        "Friendly colors, clean shapes, wide 16:9 composition, "
        "clear empty spaces for overlay sprites, "
        "suitable for children, environment only. "
        "No text, no logos, no people, no frightening elements. "
        f"Do not draw these interactive objects: {forbidden}."
    )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{model}"
    )

    print(f"[1] Gọi Cloudflare model: {model}")

    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_token}"},
            json={
                "prompt": prompt,
                "steps": 4,
            },
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(
                f"Cloudflare trả lỗi: {data.get('errors', [])}"
            )

        # Cloudflare FLUX trả ảnh mã hóa Base64.
        image_base64 = data["result"]["image"]

        # Chuyển Base64 thành dữ liệu ảnh nhị phân.
        binary = base64.b64decode(
            image_base64,
            validate=True,
        )

    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        print(f"[FAIL] Không nhận được ảnh: {exc}")
        return 1

    # Xác định PNG/JPEG bằng signature của dữ liệu ảnh.
    if binary.startswith(b"\xff\xd8\xff"):
        extension = ".jpg"
    elif binary.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = ".png"
    else:
        print("[FAIL] Kết quả không có định dạng PNG/JPEG hợp lệ.")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_file = OUTPUT_DIR / f"detective_background{extension}"
    image_file.write_bytes(binary)

    print(f"[PASS] Đã tạo ảnh: {image_file}")
    print(f"Dung lượng: {len(binary):,} bytes")
    print("CẦN XEM TAY: đúng bối cảnh, vùng trống, không vẽ nhầm vật thể.")
    print("Lưu ý: 16:9 trong prompt chưa bảo đảm kích thước ảnh.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

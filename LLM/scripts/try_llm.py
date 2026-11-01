# ============================================================
# FILE: scripts/try_llm.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Script kiểm tra nhanh LLM Server sau khi khởi động.
#
# Cách dùng (LLM Server phải đang chạy):
#   .venv/bin/python scripts/try_llm.py
#
# Địa chỉ server đọc từ biến môi trường LLM_SERVER_URL
# (mặc định http://localhost:8001). Không hardcode tham số gọi model:
# payload chỉ gửi prompt, để server dùng DEFAULT_TEMPERATURE /
# DEFAULT_MAX_OUTPUT_TOKENS cấu hình trong .env ở thư mục gốc.
#
# Script sẽ gọi lần lượt:
#   1. GET  /health
#   2. GET  /internal/llm/models
#   3. POST /internal/llm/generate (text - sinh JSON mẫu)
#   4. POST /internal/llm/generate (prompt rỗng - kiểm tra lỗi 422)
# ============================================================

import json
import os
import sys

import httpx

BASE_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8001").rstrip("/")


def main() -> int:
    ok = True

    # 1. Health
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
        body = r.json()
        print(f"[1] GET /health -> {r.status_code}")
        print(f"    provider={body['data']['provider']} | mock_mode={body['data']['mock_mode']}")
    except httpx.HTTPError as exc:
        print(f"[1] GET /health -> KHÔNG KẾT NỐI ĐƯỢC ({exc})")
        print("    Hãy chạy server trước: uvicorn app.main:app --port 8001")
        return 1

    # 2. Model list
    r = httpx.get(f"{BASE_URL}/internal/llm/models", timeout=10)
    print(f"[2] GET /internal/llm/models -> {r.status_code}")
    for m in r.json()["data"]["models"]:
        print(f"    {m['logical_name']:12s} -> {m['real_model_id']}")

    # 3. Generate thật - không gửi temperature/max_output_tokens:
    #    server tự dùng giá trị mặc định đọc từ .env (DEFAULT_*).
    payload = {
        "task": "Kiểm tra nhanh",
        "model": "generation",
        "prompt": (
            "Tạo 1 câu hỏi trắc nghiệm một đáp án về động vật cho trẻ 7 tuổi. "
            "Trả về DUY NHẤT JSON hợp lệ: "
            '{"questions": [{"question_id": "cau-01", "content": "...", '
            '"options": [{"option_id": "A", "text": "..."}], '
            '"correct_option_ids": ["A"], "explanation": "..."}]}'
        ),
    }
    try:
        r = httpx.post(f"{BASE_URL}/internal/llm/generate", json=payload, timeout=90)
        body = r.json()
        print(f"[3] POST /internal/llm/generate -> {r.status_code}")
        if body.get("success"):
            data = body["data"]
            print(f"    model={data['model']} | latency={data['latency_ms']}ms | attempts={data['attempts']}")
            print(f"    content: {data['content'][:300]}")
            try:
                json.loads(data["content"])
                print("    ✓ Content là JSON hợp lệ")
            except json.JSONDecodeError:
                print("    ! Content KHÔNG phải JSON (model có thể trả lời kèm lời dẫn)")
        else:
            ok = False
            print(f"    LỖI: [{body['error']['code']}] {body['message']}")
    except httpx.HTTPError as exc:
        ok = False
        print(f"[3] POST /internal/llm/generate -> LỖI HTTP: {exc}")

    # 4. Kiểm tra lỗi đầu vào
    r = httpx.post(
        f"{BASE_URL}/internal/llm/generate",
        json={"task": "test", "prompt": ""},
        timeout=10,
    )
    body = r.json()
    print(f"[4] POST prompt rỗng -> {r.status_code} | code={body['error']['code']}")
    if r.status_code != 422 or body["error"]["code"] != "INVALID_INPUT":
        ok = False
        print("    ! Mong đợi 422 INVALID_INPUT")

    print("\nKẾT LUẬN:", "TẤT CẢ OK ✓" if ok else "CÓ LỖI ✗")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

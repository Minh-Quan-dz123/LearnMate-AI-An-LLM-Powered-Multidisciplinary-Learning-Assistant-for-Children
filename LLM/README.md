# LLM SERVER – TÀI LIỆU BÀN GIAO (Người 4 – Hoàng Tùng)

> **Phụ trách chính:** adapter/provider, model configuration, API nội bộ, retry/timeout/rate limit, thống nhất response, hỗ trợ vision sau MVP.
> **Sản phẩm bàn giao:** LLM Server source, `.env.example`, `requirements.txt`, API contract, model list, hướng dẫn chạy.
> **Nhà cung cấp mặc định:** [OpenRouter](https://openrouter.ai) — một API key dùng được cho hàng trăm model.

---

## 1. Mục tiêu và phạm vi

**Mục tiêu:** cung cấp một service HTTP nội bộ, nhận và chuyển tiếp lời gọi model giữa Backend (EGM) và nhà cung cấp LLM, với response thống nhất, timeout/retry/rate limit.

**Có trong phạm vi:**

- `POST /internal/llm/generate`: gọi model text (sinh câu hỏi, chấm câu trả lời mở) — **MVP**.
- Ánh xạ **nhãn logic** (`generation` / `evaluation` / `vision`) sang **ID model thật** theo `.env`.
- Retry có giới hạn, timeout, rate limit, envelope response + mã lỗi thống nhất (tiếng Việt).
- `POST /internal/llm/vision`: hỗ trợ ảnh cho Module 3 — **sau MVP, đã dựng sẵn**.
- Chế độ **mock** để nhóm BE phát triển khi chưa có API key.

**Ngoài phạm vi (thuộc EGM phía BE):** xây dựng prompt nghiệp vụ, validate JSON bài tập bằng Pydantic, quyết định nội dung đúng/sai.

## 2. Công nghệ và phiên bản

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.11+ |
| Web framework | FastAPI 0.115 |
| Validation | Pydantic 2.10 + pydantic-settings 2.7 |
| HTTP client | httpx 0.28 (async) |
| Server | Uvicorn 0.34 |
| Test | pytest 8 + TestClient của FastAPI |

## 3. Cấu trúc thư mục và trách nhiệm file

```
LLM/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, endpoint, envelope, exception handler, auth nội bộ
│   ├── config.py               # Settings đọc .env + ánh xạ model (resolve_model)
│   ├── schemas.py              # Pydantic request/response
│   ├── errors.py               # AppError + mã lỗi thống nhất (422/401/429/502/503/504)
│   ├── rate_limit.py           # Sliding window rate limiter in-memory
│   ├── service.py              # Lõi: validate → rate limit → gọi provider có retry → trả metadata
│   └── providers/
│       ├── __init__.py         # build_provider() theo cấu hình PROVIDER / MOCK_MODE
│       ├── base.py             # BaseProvider + ProviderResult
│       ├── openrouter.py       # Adapter OpenRouter (OpenAI-compatible, có vision)
│       ├── openai_compat.py    # Adapter Ollama/vLLM/LM Studio... (tùy chọn)
│       └── mock.py             # Provider giả lập cho dev/test
├── tests/
│   └── test_api.py             # Test tự động (mock, không tốn chi phí)
├── docs/
│   ├── API_CONTRACT.md         # Hợp đồng API BE ↔ LLM Server
│   └── MODEL_LIST.md           # Danh sách model + tiêu chí chọn
├── requirements.txt
└── README.md                   # Tài liệu này

(thư mục GỐC dự án — bên ngoài folder LLM)
├── .env.example                # Mẫu cấu hình (commit được, KHÔNG có key thật)
├── .env                        # Cấu hình thật (đã .gitignore, KHÔNG commit)
└── .gitignore                  # Bỏ qua .env, .venv, __pycache__...
```

> **Vị trí file cấu hình:** `.env.example` và `.env` nằm ở **thư mục gốc dự án**, không nằm trong folder `LLM`. `app/config.py` luôn đọc `.env` theo đường dẫn thư mục gốc (dựa trên vị trí file, không phụ thuộc thư mục khởi động).

## 4. Luồng xử lý

```
BE (EGM) ──POST /internal/llm/generate──► FastAPI (main.py)
                                              │ 1. Auth nội bộ (X-Internal-Api-Key, nếu bật)
                                              │ 2. Pydantic validate body
                                              ▼
                                        GenerationService (service.py)
                                              │ 3. Validate prompt (rỗng / quá dài)
                                              │ 4. Rate limit (sliding window 60s)
                                              │ 5. Ánh xạ model: "generation" → MODEL_GENERATION
                                              │ 6. Gọi provider + RETRY (timeout/429/5xx, backoff lũy thừa)
                                              ▼
                                        Provider (openrouter.py)
                                              │ 7. HTTP → https://openrouter.ai/api/v1/chat/completions
                                              │ 8. Map mã lỗi provider → AppError chuẩn hóa
                                              ▼
                                        Response thống nhất
                                           200: { success, message, data: { content, model, usage, ... } }
                                           lỗi: { success:false, message: "tiếng Việt", error: { code } }
```

## 5. Endpoint tóm tắt

Xem chi tiết tại [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

| Method | Endpoint | Mục đích | Giai đoạn |
|---|---|---|---|
| `POST` | `/internal/llm/generate` | Gọi model text (sinh đề / chấm bài) | **MVP** |
| `POST` | `/internal/llm/vision` | Gọi model vision (đánh giá tranh) | Sau MVP |
| `GET` | `/internal/llm/models` | Xem model đang cấu hình | Phụ trợ |
| `GET` | `/health` | Kiểm tra server sống | Phụ trợ |
| `GET` | `/docs` | Swagger UI | Phụ trợ |

**Mẫu gọi nhanh (text):**

```bash
curl -X POST http://localhost:8001/internal/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Sinh câu hỏi trắc nghiệm",
    "model": "generation",
    "prompt": "Tạo 1 câu hỏi trắc nghiệm một đáp án về động vật cho trẻ 7 tuổi. Trả về DUY NHẤT JSON hợp lệ với keys: questions, question_id, content, options, option_id, text, correct_option_ids, explanation.",
    "temperature": 0.5,
    "max_output_tokens": 800
  }'
```

## 6. Cấu hình `.env.example` và `requirements.txt`

Xem toàn bộ chú thích trong [`.env.example`](../.env.example) (nằm ở **thư mục gốc dự án**). Các biến quan trọng nhất:

| Biến | Giá trị mẫu trong `.env.example` | Giải thích |
|---|---|---|
| `OPENROUTER_API_KEY` | *(bắt buộc khi dùng OpenRouter)* | Key lấy tại <https://openrouter.ai/keys> |
| `PROVIDER` | `openrouter` | `openrouter` \| `openai_compat` \| `mock` |
| `MODEL_GENERATION` | `openai/gpt-4o-mini` | **Bắt buộc** — model sinh câu hỏi (không còn hardcode trong code) |
| `MODEL_EVALUATION` | `openai/gpt-4o-mini` | **Bắt buộc** — model chấm câu trả lời mở |
| `MODEL_VISION` | `openai/gpt-4o-mini` | **Bắt buộc** — model vision (Module 3) |
| `MODEL_DEFAULT` | `openai/gpt-4o-mini` | **Bắt buộc** — model dùng khi nhãn logic không xác định được |
| `REQUEST_TIMEOUT_SECONDS` | `60` | Timeout một lần gọi model |
| `MAX_RETRIES` | `2` | Số lần retry khi timeout/429/5xx |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30` | Giới hạn request mỗi phút |
| `INTERNAL_API_KEY` | *(trống)* | Bật auth nội bộ giữa BE ↔ LLM Server |
| `MOCK_MODE` | `false` | `true` = trả dữ liệu mẫu, không gọi model thật |

> Toàn bộ tên model **chỉ tồn tại trong `.env` / `.env.example`**. Mã nguồn `app/config.py` khai báo các trường `MODEL_*` **bắt buộc, không có giá trị mặc định**; thiếu biến nào server báo lỗi khởi động nêu đúng biến đó.

## 7. Cách cài đặt, chạy và test

### 7.1. Cài đặt

```bash
cd LLM
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 7.2. Cấu hình

`.env.example` và `.env` nằm ở **thư mục gốc dự án** (nơi chứa `README.md`, các folder `LLM/`, `BE/`, `FE/`):

```bash
# Chạy ở thư mục gốc dự án (KHÔNG phải trong folder LLM)
cp .env.example .env
# Mở .env (thư mục gốc), điền OPENROUTER_API_KEY thật và chốt MODEL_* với cả nhóm
```

> LLM Server tự đọc `.env` theo đường dẫn thư mục gốc dự án, vì vậy vẫn đúng khi chạy `uvicorn` từ folder `LLM` hay từ thư mục gốc.

### 7.3. Chạy server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# hoặc
python -m app.main
```

Kiểm tra: mở <http://localhost:8001/health> → trả `"LLM Server đang hoạt động"`.

### 7.4. Test tự động

```bash
cd LLM
pytest -v
```

Test chạy ở chế độ **mock** (không tốn credit, không cần API key): kiểm tra envelope, mã lỗi, validate input, rate limit, ánh xạ model, vision endpoint.

### 7.5. Gọi thật lần đầu để xác nhận key hoạt động

```bash
curl -s -X POST http://localhost:8001/internal/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"task":"test","model":"generation","prompt":"Trả lời đúng một từ: bầu trời màu gì? Trả về JSON {\"answer\": \"...\"}"}'
```

Nếu key sai/hết credit → `503 LLM_UNAVAILABLE` (kiểm tra `OPENROUTER_API_KEY` tại <https://openrouter.ai/keys>).

### 7.6. Tích hợp với BE

Trong `.env` của Backend (phần Người 2/3):

```env
LLM_SERVER_URL=http://localhost:8001
LLM_TIMEOUT_SECONDS=65        # nên > REQUEST_TIMEOUT_SECONDS của LLM Server
LLM_GENERATION_MODEL=generation
LLM_EVALUATION_MODEL=evaluation
```

> Nếu bật `INTERNAL_API_KEY` ở LLM Server, BE phải gửi header `X-Internal-Api-Key` tương ứng.

## 8. Lỗi thường gặp và giải pháp

| Triệu chứng | Nguyên nhân | Giải pháp |
|---|---|---|
| `401 UNAUTHORIZED` | Sai hoặc không gửi `X-Internal-Api-Key` | Khớp giá trị giữa `.env` hai server |
| `422 INVALID_INPUT` "Prompt quá dài" | Prompt > 20000 ký tự | Rút gọn prompt hoặc tăng `MAX_PROMPT_CHARS` |
| `429 LLM_RATE_LIMITED` | Quá 30 request/phút hoặc model `:free` hết chỗ | Tăng `RATE_LIMIT_REQUESTS_PER_MINUTE`, hoặc đổi model trả phí |
| `503 LLM_UNAVAILABLE` | Sai `OPENROUTER_API_KEY`, hết credit, lỗi mạng | Kiểm tra key và tài khoản OpenRouter |
| `504 LLM_TIMEOUT` | Model phản hồi chậm quá 60s | Tăng `REQUEST_TIMEOUT_SECONDS`; kiểm tra provider |
| `502 LLM_PROVIDER_ERROR` | OpenRouter 5xx hoặc model ID sai | Đổi `MODEL_*` sang model có trên <https://openrouter.ai/models> |
| EGM báo JSON không parse được | Model trả lời kèm Markdown/quây `` ``` `` | BE nên strip code fence trước khi parse; thử model tuân JSON tốt hơn (xem `MODEL_LIST.md`) |
| Server rơi về mock dù đã có key | `MOCK_MODE=true` còn bật trong `.env` | Đặt `MOCK_MODE=false` rồi khởi động lại |

## 9. Các quyết định đã thay đổi so với tài liệu gợi ý

1. **`data` trả về nhiều trường hơn `content`**: thêm `model`, `provider`, `usage`, `latency_ms`, `attempts` (contract cũ vẫn giữ nguyên `data.content`).
2. **Nhãn logic khuyến nghị `generation`/`evaluation`/`vision`** thay vì câu tiếng Việt đầy dài; vẫn nhận biến thể tiếng Việt để không ảnh hưởng nhóm BE.
3. **Thêm `system_prompt` tùy chọn** trong request, hỗ trợ nguyên tắc "tách vùng dữ liệu và chỉ dẫn" ở README mục 8.
4. **Thêm provider `openai_compat` và chế độ `mock`**: giúp cả nhóm demo offline và không phụ thuộc 100% vào OpenRouter.
5. **Rate limit in-memory** (không Redis): đủ cho prototype chạy local/mạng nội bộ theo phạm vi README.
6. **Auth nội bộ tùy chọn** (`X-Internal-Api-Key`): README yêu cầu "cần hạn chế truy cập nội bộ hoặc secret giữa các dịch vụ" — bật/tắt được bằng `.env`, mặc định tắt cho demo nội bộ.
7. **Vị trí file cấu hình**: `.env.example` và `.env` đặt ở **thư mục gốc dự án** thay vì trong folder `LLM`; `app/config.py` neo đường dẫn `.env` theo thư mục gốc nên không phụ thuộc nơi khởi động.
8. **Không hardcode tên model**: các trường `MODEL_GENERATION/EVALUATION/VISION/DEFAULT` trong `config.py` là **bắt buộc, không có giá trị mặc định trong code**; tên model chỉ tồn tại trong `.env`. Thiếu biến → server báo lỗi khởi động chỉ rõ biến nào.

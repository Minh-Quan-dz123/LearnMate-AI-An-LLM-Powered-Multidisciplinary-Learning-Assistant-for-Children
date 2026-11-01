# API CONTRACT – LLM SERVER (Người 4 – Hoàng Tùng)

> Tài liệu bàn giao phần **API nội bộ giữa Backend (EGM) và LLM Server**.
> Envelope response thống nhất theo README mục 6.1.

## 1. Tổng quan

| Hạng mục | Giá trị |
|---|---|
| Base URL (local) | `http://localhost:8001` |
| Định dạng | JSON, header `Content-Type: application/json` |
| Endpoint MVP | `POST /internal/llm/generate` |
| Endpoint sau MVP | `POST /internal/llm/vision` |
| Endpoint phụ trợ | `GET /health`, `GET /internal/llm/models` |
| Swagger | `GET /docs` |
| Auth nội bộ (tùy chọn) | header `X-Internal-Api-Key: <INTERNAL_API_KEY>` |

**Envelope thành công:**

```json
{
  "success": true,
  "message": "Mô hình đã tạo nội dung",
  "data": { "...": "..." },
  "error": null
}
```

**Envelop lỗi:**

```json
{
  "success": false,
  "message": "Thông báo lỗi tiếng Việt",
  "data": null,
  "error": { "code": "LLM_TIMEOUT", "details": null }
}
```

## 2. `POST /internal/llm/generate` (MVP)

### 2.1. Request

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `task` | string | không | Tên tác vụ để log, VD `"Sinh câu hỏi trắc nghiệm"` |
| `model` | string | không | Nhãn logic: `generation` \| `evaluation` \| `vision` (xem §5). Để trống → model mặc định |
| `prompt` | string | **có** | Prompt do EGM phía BE xây dựng. Tối đa `MAX_PROMPT_CHARS` (mặc định 20000) ký tự |
| `temperature` | number (0–2) | không | Mặc định `0.5` |
| `max_output_tokens` | int (≥ 1) | không | Mặc định `DEFAULT_MAX_OUTPUT_TOKENS` (`.env`); vượt trần `MAX_OUTPUT_TOKENS_LIMIT` (`.env`) sẽ bị kẹp xuống trần đó |
| `system_prompt` | string | không | Nếu BE muốn tách system/data (khuyến nghị khi ghép prompt theo mục 8 của README) |

```json
{
  "task": "Sinh câu hỏi trắc nghiệm",
  "model": "generation",
  "prompt": "Hãy tạo 2 câu hỏi trắc nghiệm một đáp án về động vật và thực vật cho trẻ 7 tuổi, mức Cơ bản. Trả về DUY NHẤT JSON hợp lệ...",
  "temperature": 0.5,
  "max_output_tokens": 1800
}
```

### 2.2. Response `200`

```json
{
  "success": true,
  "message": "Mô hình đã tạo nội dung",
  "data": {
    "content": "{\"questions\":[{\"question_id\":\"cau-01\",\"content\":\"Con vật nào sống dưới nước?\",\"options\":[{\"option_id\":\"A\",\"text\":\"Con cá\"},{\"option_id\":\"B\",\"text\":\"Con gà\"}],\"correct_option_ids\":[\"A\"],\"explanation\":\"Cá sống dưới nước.\"}]}",
    "model": "openai/gpt-4o-mini",
    "provider": "openrouter",
    "task": "Sinh câu hỏi trắc nghiệm",
    "usage": { "prompt_tokens": 120, "completion_tokens": 340, "total_tokens": 460 },
    "latency_ms": 1830,
    "attempts": 1
  },
  "error": null
}
```

**Lưu ý quan trọng:**

- `data.content` là **chuỗi** (JSON string nếu prompt yêu cầu JSON). **EGM phía BE là nơi parse/validate bằng Pydantic** theo README mục 7.1.
- `data.model` là ID model **thực tế** đã dùng (sau ánh xạ), dùng để ghi vào tài liệu bàn giao/log.
- `data.usage` và `data.latency_ms` hỗ trợ theo dõi chi phí – không bắt buộc BE dùng.
- `data.attempts` = số lần đã gọi provider (bao gồm retry), hữu ích khi debug.

### 2.3. Mã lỗi

| HTTP | `error.code` | Khi nào xảy ra | BE nên xử lý thế nào |
|---|---|---|---|
| `401` | `UNAUTHORIZED` | Sai/không gửi `X-Internal-Api-Key` (khi đã bật) | Lỗi cấu hình BE ↔ LLM Server |
| `422` | `INVALID_INPUT` | `prompt` rỗng/quá dài; body sai schema; model ID sai phía provider | Không retry, trả lỗi cho FE |
| `429` | `LLM_RATE_LIMITED` | Quá `RATE_LIMIT_REQUESTS_PER_MINUTE`, hoặc provider giới hạn tần suất (sau khi retry hết lượt) | FE hiển thị "hệ thống đang bận, thử lại sau" |
| `502` | `LLM_PROVIDER_ERROR` | Lỗi 5xx từ nhà cung cấp, response thiếu trường | Có thể báo cho người dùng thử lại |
| `503` | `LLM_UNAVAILABLE` | Lỗi mạng tới provider, sai API key, hết credit | Lỗi cấu hình/ảnh hưởng vận hành |
| `504` | `LLM_TIMEOUT` | Quá `REQUEST_TIMEOUT_SECONDS` (sau khi retry hết lượt) | FE bấm `Thử lại` |
| `500` | `INTERNAL_ERROR` | Lỗi không xác định phía LLM Server | Báo log, thử lại |

Ví dụ `504`:

```json
{
  "success": false,
  "message": "Mô hình phản hồi quá lâu. Vui lòng thử lại.",
  "data": null,
  "error": { "code": "LLM_TIMEOUT", "details": null }
}
```

## 3. `POST /internal/llm/vision` (sau MVP)

Đánh giá tranh của trẻ (Module 3). Đã dựng sẵn, chỉ bật khi FE/BE sẵn sàng.

### 3.1. Request

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `task` | string | không | VD `"Đánh giá bài vẽ"` |
| `model` | string | không | Nhãn logic, khuyến nghị `vision` |
| `prompt` | string | **có** | Prompt đánh giá tranh do EGM xây dựng (mẫu §8.6 README) |
| `image_url` | string | một trong hai | URL `http(s)` của ảnh, hoặc `data:image/png;base64,...` |
| `image_base64` | string | một trong hai | Base64 thuần (không kèm tiền tố data URL) |
| `image_media_type` | string | không | Kèm `image_base64`, VD `image/png`, `image/jpeg` |
| `temperature` / `max_output_tokens` / `system_prompt` | | không | Như endpoint generate |

```json
{
  "task": "Đánh giá bài vẽ",
  "model": "vision",
  "prompt": "Bạn đang xem bức tranh do trẻ vẽ và đề bài gốc. Đề bài: Khu vườn vui vẻ...",
  "image_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "image_media_type": "image/png"
}
```

### 3.2. Response `200`

Cùng schema với `/internal/llm/generate` (`data.content` là chuỗi kết quả phân tích ảnh). Mã lỗi cũng tương tự.

> **Lưu ý:** model phải **hỗ trợ vision**. Kiểm tra cột *Vision* trong `MODEL_LIST.md`. Gọi vision bằng text-only model sẽ trả `422 INVALID_INPUT` từ provider.

## 4. `GET /internal/llm/models`

Trả danh sách model đang ánh xạ, dùng cho tài liệu nhóm và debug:

```json
{
  "success": true,
  "message": "Danh sách model đang cấu hình",
  "data": {
    "models": [
      { "logical_name": "generation", "real_model_id": "openai/gpt-4o-mini", "purpose": "Sinh câu hỏi (Module 1 & 2)" },
      { "logical_name": "evaluation", "real_model_id": "openai/gpt-4o-mini", "purpose": "Đánh giá câu trả lời mở (Module 2)" },
      { "logical_name": "vision", "real_model_id": "openai/gpt-4o-mini", "purpose": "Đánh giá bài vẽ (Module 3, sau MVP)" }
    ],
    "rate_limit_requests_per_minute": 30,
    "request_timeout_seconds": 60,
    "max_retries": 2
  }
}
```

## 5. Quy ước chọn model (ánh xạ nhãn logic)

BE gửi nhãn logic; LLM Server ánh xạ sang ID model thật theo `.env`:

| Nhãn logic BE gửi | Model thật (`.env`) | Mục đích |
|---|---|---|
| `generation` (hoặc `"Mô hình tạo nội dung mặc định"`) | `MODEL_GENERATION` | Sinh câu hỏi Module 1 & 2 |
| `evaluation` (hoặc `"Mô hình đánh giá mặc định"`) | `MODEL_EVALUATION` | Chấm câu trả lời mở Module 2 |
| `vision` | `MODEL_VISION` | Đánh giá tranh Module 3 |
| Để trống / không nhận diện được | `MODEL_DEFAULT` | Model mặc định |

Với `ALLOW_DIRECT_MODEL=true`, BE có thể gửi thẳng ID model của OpenRouter (VD `google/gemini-2.0-flash-001`). **Nhóm nên để `false`** để thống nhất model trong cả nhóm.

## 6. Cơ chế ổn định (retry / timeout / rate limit)

| Cơ chế | Cấu hình | Hành vi |
|---|---|---|
| Timeout | `REQUEST_TIMEOUT_SECONDS=60` | Quá thời gian → `504 LLM_TIMEOUT` |
| Retry | `MAX_RETRIES=2`, `RETRY_BACKOFF_SECONDS=1.0` | Chỉ retry khi timeout / 429 / lỗi mạng. Backoff lũy thừa: 1s → 2s. Lỗi đầu vào (422) **không** retry |
| Rate limit | `RATE_LIMIT_REQUESTS_PER_MINUTE=30` | Sliding window in-memory; quá hạn mức → `429 LLM_RATE_LIMITED` |
| Giới hạn kích thước | `MAX_PROMPT_CHARS=20000`, `MAX_OUTPUT_TOKENS_LIMIT=4000` (đọc từ `.env`) | Prompt quá dài → `422`; token vượt trần → tự kẹp xuống `MAX_OUTPUT_TOKENS_LIMIT`. Schema không hardcode trần nào — sửa `.env` là đổi ngay |

## 7. Thay đổi so với README gợi ý & lý do

1. **Thêm `data.model`, `data.provider`, `data.usage`, `data.latency_ms`, `data.attempts`** vào response: README chỉ nêu `data.content`; metadata thêm giúp BE log chi phí/debug mà không đổi contract cũ (vẫn giữ `data.content`).
2. **Thêm `system_prompt` tùy chọn**: README mục 8 khuyến nghị tách vùng dữ liệu/chỉ dẫn khi ghép prompt — trường này cho phép BE làm điều đó mà không đổi endpoint.
3. **Thêm `GET /health` và `GET /internal/llm/models`**: cần cho demo và tài liệu model list.
4. **`model` khuyến nghị là nhãn logic tiếng Anh** (`generation`/`evaluation`/`vision`) thay vì câu tiếng Việt dài; các biến thể tiếng Việt vẫn được chấp nhận để không ảnh hưởng BE đang làm.

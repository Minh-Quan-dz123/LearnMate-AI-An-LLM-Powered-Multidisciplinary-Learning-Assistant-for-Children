# MODEL LIST – LLM SERVER (Người 4 – Hoàng Tùng)

> LLM Server dùng **OpenRouter** (`https://openrouter.ai/api/v1`) làm nhà cung cấp mặc định.
> Model được chọn theo cấu hình `.env`; BE chỉ gửi **nhãn logic**, không biết ID model thật.

## 1. Model đang cấu hình (mặc định)

| Nhãn logic (BE gửi) | ID model thật (OpenRouter) | Loại | Vision | Ghi chú |
|---|---|---|---|---|
| `generation` | `openai/gpt-4o-mini` | Trả phí (rẻ) | ✔ | Sinh câu hỏi Module 1 & 2. Nhanh, tuân theo JSON tốt |
| `evaluation` | `openai/gpt-4o-mini` | Trả phí (rẻ) | ✔ | Chấm câu trả lời mở Module 2 |
| `vision` | `openai/gpt-4o-mini` | Trả phí (rẻ) | ✔ | Đánh giá tranh Module 3 (sau MVP) |

> `gpt-4o-mini` là model mặc định vì: rẻ, hỗ trợ cả vision (dùng lại cho Module 3), và tuân theo yêu cầu JSON chặt chẽ — phù hợp để EGM validate bằng Pydantic.

## 2. Các model thay thế đề xuất (OpenRouter)

Đổi bằng cách sửa `MODEL_GENERATION` / `MODEL_EVALUATION` / `MODEL_VISION` trong `.env`. **Không cần sửa code.**

### 2.1. Model miễn phí (`:free`) – phù hợp khi nhóm hết credit

| ID model | Loại | Vision | Ghi chú |
|---|---|---|---|
| `meta-llama/llama-3.3-70b-instruct:free` | Free | ✘ | Mạnh, tiếng Việt khá tốt |
| `google/gemma-3-27b-it:free` | Free | ✔ | Hỗ trợ vision, tốt cho bản demo |
| `qwen/qwen-2.5-72b-instruct:free` | Free | ✘ | Tuân theo JSON khá tốt |
| `mistralai/mistral-small-3.1-24b-instruct:free` | Free | ✔ | Nhỏ, nhanh, có vision |

> Model `:free` của OpenRouter có thể **hết chỗ trống giờ cao điểm** → trả `429`. Server đã tự retry; nếu vẫn lỗi, FE sẽ nhận `429 LLM_RATE_LIMITED` với thông báo tiếng Việt thân thiện.

### 2.2. Model trả phí chất lượng cao hơn

| ID model | Loại | Vision | Ghi chú |
|---|---|---|---|
| `openai/gpt-4o-mini` | Rẻ | ✔ | **Đang dùng mặc định** |
| `openai/gpt-4.1-mini` | Trung bình | ✔ | Mạnh hơn, tuân JSON rất tốt |
| `google/gemini-2.5-flash` | Trung bình | ✔ | Nhanh, rẻ, vision tốt |
| `anthropic/claude-3.5-haiku` | Trung bình | ✔ | Tiếng Việt tự nhiên |
| `meta-llama/llama-3.3-70b-instruct` | Trung bình | ✘ | Không vision |

## 3. Tiêu chí chọn model cho LearnMate AI

1. **Tuân theo JSON**: model phải trả JSON hợp lệ khi prompt yêu cầu (EGM validate bằng Pydantic và retry có giới hạn).
2. **Hỗ trợ tiếng Việt**: toàn bộ câu hỏi/lựa chọn/nhận xét phải bằng tiếng Việt tự nhiên, dễ hiểu cho trẻ 3–15 tuổi.
3. **Chi phí thấp**: mỗi request chỉ tối đa 5 câu, `max_output_tokens` ≤ 1800.
4. **Vision cho Module 3**: model đánh giá tranh phải xử lý được ảnh đầu vào.
5. **Thời gian phản hồi nhanh**: trẻ em không chờ lâu — timeout server đặt 60s, thực tế model tốt trả về trong 2–10s.

## 4. Thay đổi model trong runtime

```bash
# 1. Sửa .env
MODEL_GENERATION=google/gemini-2.5-flash

# 2. Khởi động lại LLM Server (đọc lại .env)
# 3. Kiểm tra bằng endpoint:
curl http://localhost:8001/internal/llm/models
```

## 5. Lưu ý vận hành

- **API key chỉ nằm trong `.env` của LLM Server**; FE không bao giờ thấy key.
- Model khả dụng trên OpenRouter thay đổi theo thời gian; danh sách đầy đủ: <https://openrouter.ai/models>.
- Khi chọn model mới, **cả nhóm cần chạy lại test sinh câu hỏi** để kiểm tra chất lượng JSON và tiếng Việt trước khi chốt trong hợp đồng.

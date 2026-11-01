# 🌟 LearnMate AI – Frontend (FE) Guide & Overview

> **Người phụ trách Frontend:** Đắc Quang  
> **Phiên bản:** Prototype v1.2 (React + Vite + TypeScript)  
> **Mục tiêu:** Giao diện học tập trực quan, thân thiện với trẻ em (3–15 tuổi), kết nối trực tiếp với Backend FastAPI và hỗ trợ chạy thử nghiệm độc lập qua Mock Service.

---

## 1. 🛠️ Công Nghệ & Thư Viện Chính

| Công nghệ / Thư viện | Mục đích sử dụng |
|---|---|
| **React 19 + TypeScript** | Xây dựng Single Page Application có type-safe chuẩn theo API Contract |
| **Vite** | Build tool siêu tốc, tích hợp sẵn Reverse Proxy `/api` sang `http://localhost:8000` |
| **Lucide React** | Bộ icon sinh động, trực quan (ngôi sao, cúp, nút nghe, tiếp tục, quay lại...) |
| **Canvas Confetti** | Hiệu ứng pháo hoa chúc mừng khi bé đạt điểm cao sau khi nộp bài |
| **Vanilla CSS / Modern Tokens** | Giao diện bo tròn lớn (*rounded*), màu sắc rực rỡ vui tươi, font chữ to rõ ràng |

---

## 2. 📁 Cấu Trúc Thư Mục Frontend (`src/`)

```text
FE/src/
├── types/                 # ⭐ API Contract TypeScript (User, Profile, Quiz, OpenQuestion)
│   ├── api.ts             # Chuẩn ApiResponse envelope ({ success, message, data, error })
│   ├── auth.ts            # Dữ liệu đăng ký, đăng nhập (user_id)
│   ├── child.ts           # Hồ sơ trẻ (child_id, name, age, interests)
│   └── exercise.ts        # Cấu trúc câu hỏi trắc nghiệm & câu hỏi mở
│
├── constants/             # Danh mục môn học, chủ đề chuẩn hoá theo tài liệu gốc
│   ├── subjects.ts        # Khoa học tự nhiên, Đạo đức, Kỹ năng sống + chủ đề có sẵn
│   └── config.ts          # Cấu hình API URL và cờ bật/tắt Mock Mode
│
├── services/              # Tầng kết nối mạng & Mock Data
│   ├── apiClient.ts       # Wrapper fetch / HTTP client chuẩn hoá
│   ├── authService.ts     # Gọi /api/auth/login, /api/auth/register
│   ├── childService.ts    # Gọi /api/children CRUD
│   ├── exerciseService.ts # Gọi sinh bài tập trắc nghiệm / câu hỏi mở / chấm câu mở
│   └── mocks/             # Mock data mẫu theo README để test UI độc lập với BE
│
├── components/            # Các khối giao diện tái sử dụng
│   ├── common/            # Nút bấm vui tươi, Input to rõ, Modal, Loading hoạt hình
│   ├── layout/            # Thanh điều hướng bé (Header hiển thị tên/tuổi bé đang học)
│   └── exercise/          # Thẻ câu hỏi trắc nghiệm 1 đáp án, nhiều đáp án, câu hỏi mở
│
├── views/                 # Các màn hình chính
│   ├── auth/              # Đăng ký & Đăng nhập
│   ├── profiles/          # Chọn bé đang học & Quản lý hồ sơ trẻ
│   ├── exercise/          # Cấu hình môn/chủ đề và Màn hình làm bài (Player)
│   └── result/            # Bảng điểm, nhận xét của AI và sửa bài chi tiết
│
└── utils/                 # Tiện ích logic
    └── grader.ts          # Thuật toán FE tự chấm trắc nghiệm (so sánh Set correct_option_ids)
```

---

## 3. 🔗 Cơ Chế Liên Kết Giữa FE với BE & LLM Server

Dành cho các thành viên phụ trách **Backend** hoặc **LLM Server** khi phối hợp với Frontend:

### 3.1. Nhận diện người dùng (Authentication)
- FE không gửi JWT hay Session Cookie phức tạp.
- Sau khi `POST /api/auth/login` thành công, BE chỉ cần trả về `{ "success": true, "data": { "user_id": 1, "username": "be_an" } }`.
- FE sẽ lưu `user_id` và tự động đính kèm:
  - Query param `?user_id=1` cho các phương thức `GET`, `DELETE`.
  - Thuộc tính `"user_id": 1` trong JSON body cho các phương thức `POST`, `PUT`.

### 3.2. Chấm điểm Trắc nghiệm (Module 1)
- Endpoint: `POST /api/exercises/quiz/generate`
- BE trả về đầy đủ `options` và `correct_option_ids` trong danh sách câu hỏi.
- **FE tự chấm điểm tại Client** bằng cách so sánh tập hợp phương án bé chọn và `correct_option_ids`. **Không gọi BE khi nộp bài trắc nghiệm**.

### 3.3. Chấm điểm Câu hỏi mở (Module 2)
- Endpoint sinh câu hỏi: `POST /api/exercises/open/generate`
- Endpoint chấm điểm: `POST /api/exercises/open/evaluate`
- Khi bé nhập xong câu trả lời, FE gửi payload gồm: `child_id`, `question_id`, `question`, `answer`, `evaluation_criteria`, `subject`, `topic`, `level`.
- BE gọi LLM để đánh giá ngữ nghĩa và trả về: `score` (0–10), `feedback`, `strengths`, `suggestions`, `sample_answer`.

### 3.4. Cấu hình Cổng Mạng (Dev Proxy)
- Vite Dev Server chạy tại: `http://localhost:5173`
- Toàn bộ request bắt đầu bằng `/api/...` được tự động chuyển hướng (Proxy) tới Backend tại: `http://localhost:8000`
- Các bạn làm BE chỉ cần khởi chạy FastAPI ở port `8000`, FE không cần chỉnh sửa địa chỉ URL và không bị chặn bởi CORS.

---

## 4. 🚀 Hướng Dẫn Chạy Thử Frontend

```bash
# 1. Cài đặt thư viện (nếu chưa cài)
npm install

# 2. Khởi chạy môi trường phát triển (Dev Server)
npm run dev
# Mở trình duyệt tại: http://localhost:5173

# 3. Chuyển đổi chế độ Mock (Nếu BE chưa bật hoặc chưa xong API):
# Chỉnh sửa src/constants/config.ts -> USE_MOCK_DATA = true
```

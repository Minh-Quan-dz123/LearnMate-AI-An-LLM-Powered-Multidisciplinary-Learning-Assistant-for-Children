# LEARNMATE AI – TÀI LIỆU GỢI Ý PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

**AI Learning Companion for Kids · Bản thử nghiệm v1.2 · 22/10/2026**

> **Phạm vi quan trọng:** Đây là **prototype phục vụ thử nghiệm khả năng sinh câu hỏi và đánh giá của LLM**, chạy trong môi trường local/demo với dữ liệu giả. Không phải sản phẩm production, không cần JWT, cookie phiên, phân quyền hay hệ thống bảo mật phức tạp. Ưu tiên code đơn giản, dễ kiểm thử và thay đổi model.

> **Tính chất tài liệu:** Đây là **tài liệu định hướng triển khai**, không phải đặc tả bắt buộc 100%. Ví dụ giao diện, bảng dữ liệu, đường dẫn API, prompt và JSON là **đề xuất cụ thể để nhóm thảo luận và áp dụng**. Lập trình viên được thay đổi cách tổ chức mã nguồn, framework, tên trường và chiến lược xử lý khi có lý do hợp lý. Tuy nhiên, những giao diện kết nối giữa FE ↔ BE ↔ LLM Server phải **được cả nhóm thống nhất và ghi lại trong API contract** trước khi tích hợp.

## 1. Tổng quan và phạm vi

### 1.1. Mục tiêu

LearnMate AI hỗ trợ trẻ em học tập thông qua bài tập được AI tạo theo **môn học, chủ đề, mức độ và độ tuổi**. Hệ thống ưu tiên câu hỏi ngắn, dễ hiểu, phù hợp lứa tuổi, phản hồi tích cực. Tài liệu gốc mô tả ba nhóm môn học: **Khoa học tự nhiên, Đạo đức, Kỹ năng sống** (có thể mở rộng môn khác).

### 1.2. Đối tượng sử dụng

Bản thử nghiệm chỉ có **một loại tài khoản người dùng**, dùng để đăng nhập và quản lý hồ sơ trẻ. Không cần triển khai vai trò admin, phụ huynh hay giáo viên riêng trong v1. Một tài khoản **có thể quản lý một hoặc nhiều hồ sơ trẻ** là đề xuất mở rộng dễ áp dụng; nếu muốn đơn giản tối đa, MVP có thể giới hạn một hồ sơ cho mỗi tài khoản.

### 1.3. Phạm vi sản phẩm

- **MVP bắt buộc:** đăng ký, đăng nhập/đăng xuất, tạo/xem/sửa/xóa hồ sơ trẻ; chọn cấu hình bài tập; sinh và hiển thị **trắc nghiệm một đáp án**, **trắc nghiệm nhiều đáp án**, **câu trả lời mở**; hiển thị kết quả và phản hồi.
- **Chấm trắc nghiệm:** FE tự chấm dựa trên đáp án đã được BE trả về, **không bắt buộc lưu bài làm hoặc gọi BE khi chấm**.
- **Chấm câu trả lời mở:** FE gửi câu hỏi và câu trả lời tới BE; EGM gọi LLM để đánh giá theo ý nghĩa.
- **Định hướng sau MVP:** bài tập vẽ trên canvas, đánh giá hình ảnh qua vision model, tùy chọn tạo hình ảnh hoàn thiện; lịch sử luyện tập, bảng tiến độ, thống kê.
- **Giới hạn thử nghiệm:** tối đa **5 câu cho mỗi lần sinh**; mức độ **Cơ bản / Nâng cao**, không bổ sung các nhãn Dễ/Trung bình/Khó.

### 1.4. Quy ước dùng chung

- Toàn bộ nội dung người dùng nhìn thấy, nhãn màn hình, lời nhắc, câu hỏi, lựa chọn, nhận xét, thông báo lỗi và **giá trị chuỗi thể hiện nội dung nghiệp vụ trong ví dụ JSON** viết bằng **tiếng Việt**. **Tên key JSON** giữ **tiếng Anh** (`subject`, `topic`, `question_type`, `feedback`...).
- Ngoại lệ đương nhiên: giá trị kỹ thuật như ID, URL, thời gian ISO, mã lỗi, API token, định dạng MIME, tên model và các mã định danh không phải văn bản hiển thị.
- Mỗi ví dụ là **một phương án contract**. Nếu chọn dùng các chuỗi tiếng Việt như `"level": "Cơ bản"` và `"question_type": "Trắc nghiệm một đáp án"`, FE/BE phải dùng đồng nhất; có thể sau này đổi sang mã enum cố định nếu cần, nhưng UI vẫn hiển thị tiếng Việt.
- HTTP status dùng chuẩn: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `502`, `503`, `504`. Lỗi hiển thị cho người dùng phải là tiếng Việt.
- Điểm ví dụ thống nhất **thang 10**, làm tròn một chữ số thập phân khi hiển thị. Khuyến nghị cho phép `score` là số thực trong `[0,10]`.

## 2. Kiến trúc đề xuất

```text
Trình duyệt / Web Frontend (React hoặc Next.js)
     │ HTTP + JSON
     ▼
Backend API (Python + FastAPI + Pydantic)
     ├── Quản lý tài khoản, hồ sơ trẻ ──► PostgreSQL / Supabase
     ├── Module 1: Trắc nghiệm
     ├── Module 2: Câu trả lời mở
     ├── Module 3: Vẽ (sau MVP)
     └── Exercise Generation Module (EGM)
                  │ HTTP + JSON
                  ▼
        LLM Server (Python + FastAPI + SDK)
                  ├── Text model: sinh câu hỏi
                  ├── Text model: đánh giá câu trả lời
                  └── Vision / Image model: sau MVP
```

### 2.1. Frontend

**Trách nhiệm:** giao diện, quản lý hồ sơ đang chọn, form cấu hình bài, gọi API, loading/error, render câu hỏi theo `question_type`, thu đáp án, chấm trắc nghiệm cục bộ, gửi đáp án mở để chấm. Gợi ý công nghệ: React + TypeScript + Tailwind CSS **hoặc** Next.js + TypeScript + Tailwind CSS. Không bắt buộc dùng một thư viện quản lý state cụ thể.

**Tách component tham khảo:** `AuthPage`, `ChildProfilePage`, `ExerciseConfigForm`, `ExercisePlayer`, `SingleChoiceQuestion`, `MultipleChoiceQuestion`, `OpenEndedQuestion`, `ResultPage`, `LoadingState`, `ErrorNotice`; `DrawingCanvas` dành cho tương lai. Có thể dùng route hoặc hiển thị theo step, miễn luồng dễ hiểu.

### 2.2. Backend API

**Trách nhiệm:** kiểm tra dữ liệu đầu vào, quản lý người dùng/hồ sơ, tạo prompt bằng EGM, gọi LLM Server, chuẩn hóa và xác thực đầu ra, trả kết quả thống nhất. Nên chia router/service/schemas riêng nhưng không bắt buộc microservice. Gợi ý: Python + FastAPI + Pydantic, PostgreSQL với driver/ORM do người triển khai quyết định.

**Ví dụ cấu trúc:** `app/main.py`, `app/routers/auth.py`, `children.py`, `exercises.py`, `app/services/child_service.py`, `exercise_generation.py`, `app/schemas/`, `app/db/`, `app/core/config.py`, `tests/`. Nhóm có thể chia các router Module 1 và 2 nhưng nên chạy **chung một FastAPI app**, tránh xung đột API và cấu hình DB.

### 2.3. LLM Server

**Trách nhiệm:** nhận request chuẩn từ BE, chọn nhà cung cấp/model theo cấu hình, gửi prompt, nhận nội dung/model output, chuyển thành response thống nhất, xử lý timeout/rate limit/lỗi. **Không sở hữu prompt nghiệp vụ**: prompt sinh câu hỏi/chấm bài thuộc EGM phía BE. LLM Server có thể kết nối model cloud hoặc local, một hoặc nhiều model.

**Đề xuất tính ổn định:** cấu hình `MODEL_GENERATION`, `MODEL_EVALUATION` (có thể trùng nhau), timeout và giới hạn token trong `.env`; không trả chi tiết secret/API key về trình duyệt.

## 3. Thiết kế database – ĐỀ XUẤT

### 3.1. Nguyên tắc

MVP **chỉ cần hai bảng chính** để đúng tinh thần đơn giản của tài liệu gốc: `users` và `child_profiles`. Trắc nghiệm FE tự chấm nên **không cần** bảng `questions` / `answers`. Câu trả lời mở cũng có thể chấm theo request, không cần lưu lịch sử. Các bảng lịch sử là **tùy chọn**, không được coi là điều kiện hoàn thành MVP.

### 3.2. Bảng `users` (bắt buộc)

| Trường | Kiểu PostgreSQL đề xuất | Ràng buộc / Ý nghĩa |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | Khóa chính |
| `username` | `VARCHAR(60)` | `UNIQUE NOT NULL`, không phân biệt chữ hoa/thường khi kiểm tra trùng nếu nhóm chọn quy tắc đó |
| `password` | `TEXT` | `NOT NULL`, mật khẩu demo; ưu tiên dữ liệu giả, không sử dụng mật khẩu thật |
| `created_at` | `TIMESTAMPTZ` | Mặc định thời gian tạo |
| `updated_at` | `TIMESTAMPTZ` | Cập nhật khi thay đổi |

**Lưu ý:** chỉ cần `username` + `password`, không cần email, số điện thoại, JWT hoặc session. Để giảm tối đa phần việc ngoài LLM, prototype có thể lưu mật khẩu demo đơn giản trong DB; **chỉ dùng mật khẩu giả và không công khai server**, không đưa mật khẩu thật của bất kỳ ai vào hệ thống.

### 3.3. Bảng `child_profiles` (bắt buộc)

| Trường | Kiểu PostgreSQL đề xuất | Ràng buộc / Ý nghĩa |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | Khóa chính |
| `user_id` | `BIGINT` | `NOT NULL`, FK → `users.id` |
| `name` | `VARCHAR(100)` | Tên/biệt danh trẻ, `NOT NULL` |
| `age` | `SMALLINT` | Tuổi; ví dụ kiểm tra 3–15 khi nhận request, có thể điều chỉnh |
| `gender` | `VARCHAR(30)` | Tùy chọn: `Nam`, `Nữ`, `Không muốn cung cấp` |
| `interests` | `TEXT[]` hoặc `JSONB` | Danh sách sở thích tiếng Việt; mặc định rỗng |
| `created_at` | `TIMESTAMPTZ` | Thời gian tạo |
| `updated_at` | `TIMESTAMPTZ` | Thời gian cập nhật |

Quan hệ: **1 user → N child_profiles** (nếu chỉ hỗ trợ 1 hồ sơ thì thêm `UNIQUE(user_id)`). Xóa tài khoản có thể `ON DELETE CASCADE`; nếu xóa hồ sơ riêng thì nhóm có thể kiểm tra quan hệ `user_id` – `child_id` để tránh sửa nhầm dữ liệu demo (không phải xác thực bảo mật).

### 3.4. SQL DDL minh họa

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(60) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE child_profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    age SMALLINT NOT NULL CHECK (age BETWEEN 3 AND 15),
    gender VARCHAR(30),
    interests TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_child_profiles_user_id ON child_profiles(user_id);
```

**Ghi chú:** đây là SQL minh họa, không phải schema bắt buộc. Nếu dùng Supabase, Backend có thể kết nối **trực tiếp PostgreSQL bằng connection string**; không bắt buộc thao tác thông qua Supabase HTTP API. Cần cấu hình kết nối TLS/transaction pooler theo môi trường.

### 3.5. Bảng tùy chọn – chỉ triển khai khi cần

| Bảng | Mục đích | Dữ liệu đề xuất |
|---|---|---|
| `exercise_sessions` | Lịch sử một lần luyện tập | `id`, `child_id`, `module`, `subject`, `topic`, `level`, `score`, `created_at` |
| `exercise_attempts` | Chi tiết bài làm (chỉ khi cần thống kê) | `session_id`, `question_snapshot JSONB`, `answer JSONB`, `score`, `feedback` |
| `drawing_submissions` | Lưu bài vẽ (tương lai) | `child_id`, `drawing_url`, `task_snapshot JSONB`, `evaluation JSONB`, `created_at` |

Prototype nên dùng tên/tuổi giả và không lưu ảnh cá nhân thật. Nếu thử Module 3 có thể lưu tạm file ảnh và xóa sau buổi demo; không cần thêm bảng nếu chưa dùng.

## 4. Gợi ý thiết kế giao diện (FE)

### 4.1. Danh sách màn hình

| Màn hình | Thành phần / nút bằng tiếng Việt | Hành vi |
|---|---|---|
| Đăng ký | `Tên đăng nhập`, `Mật khẩu`, `Xác nhận mật khẩu`, nút `Tạo tài khoản` | Kiểm tra dữ liệu, báo trùng tên, chuyển sang đăng nhập |
| Đăng nhập | `Tên đăng nhập`, `Mật khẩu`, `Đăng nhập`, `Chưa có tài khoản? Đăng ký` | Thành công → chọn hồ sơ trẻ |
| Chọn hồ sơ | `Chọn người học`, thẻ `Bé An`, `Thêm hồ sơ`, `Chỉnh sửa`, `Xóa` | Chọn `child_id` đang dùng |
| Tạo/Sửa hồ sơ | `Tên hoặc biệt danh`, `Tuổi`, `Giới tính (không bắt buộc)`, `Sở thích`, `Lưu hồ sơ` | Có thể chọn nhiều sở thích |
| Chọn module | `Trắc nghiệm`, `Trả lời câu hỏi`, `Bài tập vẽ (sắp ra mắt)` | Module 3 ẩn hoặc vô hiệu trong MVP |
| Cấu hình bài | `Môn học`, `Chủ đề`, `Nhập chủ đề khác`, `Mức độ`, `Dạng bài`, `Số câu (1–5)`, `Tạo bài tập` | Hiện các trường phù hợp module |
| Làm bài | `Câu 1/5`, câu hỏi, lựa chọn/ô nhập, `Câu trước`, `Câu tiếp`, `Nộp bài` | Không mất câu đã chọn khi chuyển câu |
| Kết quả | `Điểm của con`, `Số câu đúng`, `Lời giải`, `Nhận xét`, `Làm bài mới` | Trắc nghiệm tự chấm; câu mở hiển thị đánh giá AI |
| Bài vẽ (tương lai) | `Đề bài vẽ`, `Bảng vẽ`, `Xóa nét`, `Hoàn tác`, `Gửi tranh`, `Xem nhận xét` | Upload hình, nhận đánh giá vision |

### 4.2. Gợi ý bố cục các màn hình chính

**Màn hình cấu hình bài:** phía trên hiển thị tên/tuổi trẻ đang chọn, tiêu đề `Hôm nay con muốn học gì?`. Bên dưới là các bộ chọn môn học → chủ đề → mức độ → dạng bài → số câu. Khi chọn `Chủ đề khác`, xuất hiện ô `Nhập chủ đề con muốn học`. Nút chính: `Tạo bài tập`. Chỉ cho gửi khi các trường hợp lệ.

**Màn hình làm trắc nghiệm:** mỗi câu nằm trong thẻ riêng, chữ lớn, mỗi lựa chọn một hàng. Trắc nghiệm một đáp án dùng radio; nhiều đáp án dùng checkbox và gợi ý `Có thể chọn nhiều đáp án`. Khi bấm `Nộp bài`, FE chấm một lần và khóa hoặc đánh dấu bài đã nộp. Không hiện đáp án đúng trước khi nộp.

**Màn hình câu mở:** hiển thị câu hỏi và textarea có placeholder `Con hãy viết câu trả lời của mình ở đây...`. Khi bấm `Kiểm tra câu trả lời`, hiển thị `AI đang đọc câu trả lời của con...`; nếu lỗi, nút `Thử lại` giữ nguyên nội dung đã nhập. Có thể chấm từng câu hoặc chấm toàn bộ bài – nhóm FE/BE cần thống nhất trước.

### 4.3. State gợi ý

```ts
// Ví dụ minh họa, không bắt buộc đúng tên property này
interface ExerciseState {
  childId: number;
  questions: Question[];
  currentIndex: number;
  selectedAnswers: Record<string, string[]>;
  textAnswers: Record<string, string>;
  isSubmitted: boolean;
  isLoading: boolean;
  errorMessage: string | null;
  score: number | null;
}
```

**Trạng thái lỗi nên chuẩn bị:** không có hồ sơ trẻ, chưa chọn chủ đề, số câu ngoài 1–5, không sinh được bài, response sai schema, mạng chậm, hết hạn phiên, LLM đang bận. Thông báo hiển thị phải dễ hiểu và không đổ lỗi cho trẻ.

## 5. Nội dung môn học, chủ đề và loại bài

### 5.1. Môn học/chủ đề gợi ý

| Môn học | Các chủ đề có sẵn trên FE |
|---|---|
| **Khoa học tự nhiên** | Động vật và thực vật; Cơ thể người; Môi trường và tài nguyên thiên nhiên; Vật chất và năng lượng; Trái Đất và bầu trời |
| **Đạo đức** | Yêu thương gia đình; Kính trọng thầy cô, lễ phép với người lớn; Đoàn kết, giúp đỡ bạn bè; Trung thực; Chăm chỉ, có trách nhiệm; Tuân thủ quy định nơi công cộng; Bảo vệ của công |
| **Kỹ năng sống** | Kỹ năng giao tiếp; Kỹ năng quản lý cảm xúc; Kỹ năng tự phục vụ; Kỹ năng làm việc nhóm; Kỹ năng giải quyết vấn đề; Kỹ năng tự bảo vệ bản thân; Kỹ năng xử lý tình huống nguy hiểm |

Mỗi môn có tùy chọn `Ngẫu nhiên` và `Chủ đề khác (tự nhập)`. Danh sách này có thể hardcode ở FE trong MVP, hoặc BE trả về qua API catalog nếu cần mở rộng. **Module 1 và Module 2 cùng sử dụng danh sách môn/chủ đề trên** theo tài liệu gốc.

### 5.2. Ba loại câu hỏi của MVP

| Giá trị `question_type` đề xuất | Hiển thị tiếng Việt | Cách chấm |
|---|---|---|
| `Trắc nghiệm một đáp án` | Chọn 1 phương án | FE: tập ID đã chọn = tập ID đáp án đúng |
| `Trắc nghiệm nhiều đáp án` | Chọn tất cả phương án đúng | FE: so sánh hai tập ID, **không quan tâm thứ tự** |
| `Câu trả lời mở` | Điền từ/cụm từ/danh sách/câu ngắn | BE → EGM → LLM đánh giá theo ý nghĩa |

**Nguyên tắc:** Với nhiều đáp án, N là số đáp án đúng được sinh theo từng câu, không phải số đáp án mà FE tự đoán. Nên yêu cầu tối thiểu 2 đáp án đúng, tổng số phương án 3–5; EGM kiểm tra ràng buộc trước khi trả FE.

## 6. Hợp đồng API FE ↔ BE – GỢI Ý THỐNG NHẤT

### 6.1. Quy tắc request/response

- Base path ví dụ: `/api`; body JSON, header `Content-Type: application/json`.
- Responses thành công: `{ "success": true, "message": "...", "data": ... }`; responses lỗi: `{ "success": false, "message": "...", "error": { "code": "..." } }`.
- **Cơ chế định danh đơn giản cho demo:** đăng nhập kiểm tra `username` và `password` một lần; BE trả về `user_id` sau khi đăng nhập thành công; FE giữ `user_id` trong state hoặc `localStorage` và gửi kèm các request cần xác định tài khoản. `username` chỉ dùng cho đăng ký và đăng nhập. **Không dùng JWT, session hay cookie đăng nhập**. Đây chỉ là cách nhận diện dữ liệu thử nghiệm, **không xác thực được người gửi request**; chỉ chạy local/mạng nội bộ tin cậy, không công khai internet và không sử dụng dữ liệu thật.
- Với `GET`/`DELETE`, có thể truyền `user_id` bằng query string; với `POST`/`PUT`, gửi `user_id` trong JSON body. `child_id` xác định hồ sơ trẻ đang thao tác. FE xóa `user_id` khỏi state/localStorage khi bấm Đăng xuất (không cần endpoint logout).

### 6.2. Danh mục endpoint

| Method | Endpoint gợi ý | Chức năng | Ai dùng | Phạm vi |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | Đăng ký | FE | MVP |
| `POST` | `/api/auth/login` | Đăng nhập | FE | MVP |
| `GET` | `/api/children` | Danh sách hồ sơ trẻ | FE | MVP |
| `POST` | `/api/children` | Tạo hồ sơ trẻ | FE | MVP |
| `GET` | `/api/children/{child_id}` | Xem chi tiết hồ sơ | FE | MVP |
| `PUT` | `/api/children/{child_id}` | Cập nhật hồ sơ | FE | MVP |
| `DELETE` | `/api/children/{child_id}` | Xóa hồ sơ | FE | MVP |
| `POST` | `/api/exercises/quiz/generate` | Sinh trắc nghiệm | FE | MVP |
| `POST` | `/api/exercises/open/generate` | Sinh câu hỏi mở | FE | MVP |
| `POST` | `/api/exercises/open/evaluate` | Chấm câu trả lời mở | FE | MVP |
| `GET` | `/api/catalog/subjects` | Danh sách môn/chủ đề | FE | Tùy chọn, có thể hardcode FE |
| `POST` | `/api/exercises/drawing/generate` | Sinh đề vẽ | FE | Sau MVP |
| `POST` | `/api/exercises/drawing/evaluate` | Upload ảnh và đánh giá | FE | Sau MVP |
| `POST` | `/internal/llm/generate` | BE gửi tác vụ text tới LLM Server | BE | API nội bộ |
| `POST` | `/internal/llm/vision` | BE gửi tác vụ ảnh tới LLM Server | BE | Sau MVP |

**Không cần** `/api/exercises/quiz/evaluate` vì FE tự chấm. `GET /api/children/me` và `PUT /api/children/me` từ tài liệu ban đầu chỉ phù hợp nếu **mỗi tài khoản có đúng 1 hồ sơ trẻ**; bảng trên chọn `{child_id}` để hỗ trợ nhiều hồ sơ. Nhóm có thể chọn một trong hai hướng.

### 6.3. Đăng ký, đăng nhập và hồ sơ trẻ – JSON mẫu

**Đăng ký:** `POST /api/auth/register`.

```json
{
  "username": "be_an_01",
  "password": "MatKhauDemo123",
  "confirm_password": "MatKhauDemo123"
}
```

`confirm_password` nên được FE kiểm tra và **có thể không gửi lên BE** nếu nhóm thống nhất; BE chỉ cần kiểm tra trường không rỗng; không bắt buộc có quy tắc độ mạnh mật khẩu. Response `201`:

```json
{
  "success": true,
  "message": "Tạo tài khoản thành công",
  "data": { "user_id": 1, "username": "be_an_01" }
}
```

**Đăng nhập:** `POST /api/auth/login` với `{ "username": "be_an_01", "password": "MatKhauDemo123" }`. Response `200` trả về `user_id` để FE ghi nhớ tạm (có thể trả thêm `username` để hiển thị); không trả token:

```json
{
  "success": true,
  "message": "Đăng nhập thành công",
  "data": { "user_id": 1, "username": "be_an_01" }
}
```

**Tạo hồ sơ:** `POST /api/children`:

```json
{
  "user_id": 1,
  "name": "Bé An",
  "age": 7,
  "gender": "Nữ",
  "interests": ["Động vật", "Vẽ tranh", "Âm nhạc"]
}
```

Response `201`:

```json
{
  "success": true,
  "message": "Tạo hồ sơ trẻ thành công",
  "data": {
    "child_id": 101,
    "user_id": 1,
    "name": "Bé An",
    "age": 7,
    "gender": "Nữ",
    "interests": ["Động vật", "Vẽ tranh", "Âm nhạc"]
  }
}
```

**Danh sách:** `GET /api/children?user_id=1` → `data` là mảng hồ sơ như trên. **Chi tiết:** `GET /api/children/101?user_id=1`. **Cập nhật:** `PUT /api/children/101` với body gồm `user_id` và các trường như khi tạo. **Xóa:** `DELETE /api/children/101?user_id=1` → `{ "success": true, "message": "Đã xóa hồ sơ trẻ", "data": null }`.

### 6.4. Module 1 – Sinh trắc nghiệm

**Request:** `POST /api/exercises/quiz/generate`:

```json
{
  "child_id": 101,
  "subject": "Khoa học tự nhiên",
  "topic": "Động vật và thực vật",
  "level": "Cơ bản",
  "question_type": "Trắc nghiệm một đáp án",
  "question_count": 2
}
```

**Response `200` – ví dụ một đáp án:**

```json
{
  "success": true,
  "message": "Tạo bài tập thành công",
  "data": {
    "exercise_id": "demo-bai-001",
    "subject": "Khoa học tự nhiên",
    "topic": "Động vật và thực vật",
    "level": "Cơ bản",
    "question_type": "Trắc nghiệm một đáp án",
    "questions": [
      {
        "question_id": "cau-01",
        "content": "Con vật nào dưới đây sống dưới nước?",
        "options": [
          { "option_id": "A", "text": "Con mèo" },
          { "option_id": "B", "text": "Con cá" },
          { "option_id": "C", "text": "Con gà" }
        ],
        "correct_option_ids": ["B"],
        "explanation": "Cá sống dưới nước và dùng mang để hô hấp."
      },
      {
        "question_id": "cau-02",
        "content": "Bộ phận nào giúp cây hút nước từ đất?",
        "options": [
          { "option_id": "A", "text": "Rễ" },
          { "option_id": "B", "text": "Hoa" },
          { "option_id": "C", "text": "Quả" }
        ],
        "correct_option_ids": ["A"],
        "explanation": "Rễ cây hút nước và chất dinh dưỡng từ đất."
      }
    ]
  }
}
```

**Biến thể nhiều đáp án:** giữ nguyên schema, chỉ đổi `question_type` thành `Trắc nghiệm nhiều đáp án`; ví dụ một câu:

```json
{
  "question_id": "cau-03",
  "content": "Những con vật nào sau đây có thể bay?",
  "options": [
    { "option_id": "A", "text": "Chim sẻ" },
    { "option_id": "B", "text": "Con bò" },
    { "option_id": "C", "text": "Bướm" },
    { "option_id": "D", "text": "Con cá" }
  ],
  "correct_option_ids": ["A", "C"],
  "explanation": "Chim sẻ và bướm đều có thể bay."
}
```

**FE tự chấm – đề xuất:** với mỗi câu, biến lựa chọn thành **tập hợp ID**, so sánh bằng nhau với tập `correct_option_ids`. Đúng hoàn toàn được 1 điểm câu; sai hoặc thiếu/thừa lựa chọn là 0 điểm câu (không chấm một phần trong MVP). `score = 10 × số_câu_đúng / tổng_số_câu`. Chỉ hiển thị đáp án và giải thích sau khi nộp. **Lưu ý:** do đáp án đúng có trong payload FE, người có công cụ trình duyệt có thể xem được; phù hợp demo học tập, **không phù hợp bài thi cần bảo mật đáp án**.

**EGM phải kiểm tra:** `questions.length == question_count`, ID câu/phương án không trùng, `correct_option_ids` đều tồn tại trong `options`, một đáp án có đúng 1 ID, nhiều đáp án có tối thiểu 2 ID, `content` không rỗng; bài tập phù hợp độ tuổi/môn/chủ đề. Khi output sai schema, có thể thử sinh lại có giới hạn rồi trả lỗi tiếng Việt.

### 6.5. Module 2 – Sinh và chấm câu trả lời mở

**Sinh câu hỏi:** `POST /api/exercises/open/generate`:

```json
{
  "child_id": 101,
  "subject": "Kỹ năng sống",
  "topic": "Kỹ năng giao tiếp",
  "level": "Cơ bản",
  "question_type": "Câu trả lời mở",
  "question_count": 2
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Tạo câu hỏi thành công",
  "data": {
    "exercise_id": "demo-mo-001",
    "question_type": "Câu trả lời mở",
    "questions": [
      {
        "question_id": "cau-01",
        "content": "Khi thấy một người bạn bị ngã, con sẽ làm gì?",
        "answer_hint": "Con hãy viết một hoặc hai câu ngắn.",
        "evaluation_criteria": ["Biết quan tâm và giúp đỡ bạn", "Biết gọi người lớn khi cần"]
      },
      {
        "question_id": "cau-02",
        "content": "Khi muốn mượn đồ chơi của bạn, con nên nói như thế nào?",
        "answer_hint": "Con có thể viết một câu lịch sự.",
        "evaluation_criteria": ["Biết xin phép", "Dùng lời nói lịch sự"]
      }
    ]
  }
}
```

**Chấm từng câu (phương án đơn giản):** `POST /api/exercises/open/evaluate`. Chọn cách gửi đầy đủ câu hỏi/tiêu chí vì BE **không bắt buộc lưu đề bài**, nhưng BE phải kiểm tra kích thước dữ liệu và không tin hoàn toàn nội dung FE gửi.

```json
{
  "child_id": 101,
  "question_id": "cau-01",
  "question": "Khi thấy một người bạn bị ngã, con sẽ làm gì?",
  "answer": "Con sẽ đỡ bạn dậy và gọi cô giáo nếu bạn bị đau.",
  "evaluation_criteria": ["Biết quan tâm và giúp đỡ bạn", "Biết gọi người lớn khi cần"],
  "subject": "Kỹ năng sống",
  "topic": "Kỹ năng giao tiếp",
  "level": "Cơ bản"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Đã đánh giá câu trả lời",
  "data": {
    "question_id": "cau-01",
    "score": 10,
    "is_appropriate": true,
    "feedback": "Con đã biết quan tâm và giúp đỡ bạn. Rất tốt!",
    "strengths": ["Biết giúp bạn đứng dậy", "Biết nhờ cô giáo hỗ trợ"],
    "suggestions": ["Con có thể hỏi thêm xem bạn có đau nhiều không."],
    "sample_answer": "Con sẽ hỏi thăm, giúp bạn nếu an toàn và báo cô giáo khi cần."
  }
}
```

**Chấm trọn bộ bài:** không bắt buộc trong MVP. Nếu chọn, có thể tạo endpoint `/api/exercises/open/evaluate-batch` trả `results[]` và điểm trung bình; FE/BE phải thống nhất để tránh gọi một câu nhiều lần hoặc chấm nhầm tổng điểm.

**Lưu ý chấm điểm:** LLM chấm theo ý nghĩa, chấp nhận cách diễn đạt đa dạng, lỗi chính tả nhỏ và câu ngắn; không ép trẻ dùng đúng từng chữ. `score` là **đánh giá tham khảo của AI**, không khẳng định chính xác tuyệt đối. Nếu câu trả lời trống: BE trả `422` với thông báo `Con hãy nhập câu trả lời trước khi kiểm tra.`. Nếu AI không chắc, phản hồi nên nói cần người lớn hỗ trợ thay vì tự khẳng định.

### 6.6. Module 3 – Vẽ (tương lai, không phải điều kiện nghiệm thu MVP)

**Sinh đề:** `POST /api/exercises/drawing/generate`:

```json
{
  "child_id": 101,
  "topic": "Khu vườn vui vẻ",
  "level": "Cơ bản",
  "required_detail_count": 3
}
```

Response:

```json
{
  "success": true,
  "message": "Đã tạo đề bài vẽ",
  "data": {
    "drawing_task_id": "ve-001",
    "title": "Khu vườn của bé",
    "description": "Con hãy vẽ một khu vườn có mặt trời, một cái cây và hai bông hoa. Con có thể tô màu theo sở thích.",
    "required_details": ["Một mặt trời", "Một cái cây", "Hai bông hoa"],
    "encouragement": "Con hãy thỏa sức sáng tạo nhé!"
  }
}
```

**Đánh giá ảnh:** đề xuất dùng `multipart/form-data` gồm `image` (PNG/JPEG), `drawing_task_id`, `description`, `required_details` (JSON string), `child_id`. BE kiểm tra dung lượng/MIME/kích thước ảnh, rồi gọi LLM Server vision; không bắt buộc lưu ảnh vĩnh viễn.

Response:

```json
{
  "success": true,
  "message": "Đã nhận xét bức tranh",
  "data": {
    "score": 8.5,
    "found_details": ["Mặt trời", "Cái cây"],
    "missing_details": ["Hai bông hoa"],
    "feedback": "Bức tranh của con rất đáng yêu! Con đã vẽ mặt trời và cây rất rõ.",
    "suggestions": ["Con thử thêm hai bông hoa nhiều màu sắc nhé!"],
    "completed_image_url": null
  }
}
```

**Hoàn thiện bằng AI (tùy chọn):** BE gọi thêm image-to-image/sketch-to-image, nhận URL ảnh hoặc file và hiển thị **tranh gốc** cạnh **tranh được AI hoàn thiện**; phải ghi rõ đâu là ảnh của trẻ, đâu là ảnh AI và tránh để AI thay thế lời nhận xét về sự sáng tạo của trẻ.

### 6.7. Response lỗi chuẩn

Ví dụ `422`:

```json
{
  "success": false,
  "message": "Số câu hỏi phải từ 1 đến 5.",
  "error": { "code": "INVALID_QUESTION_COUNT", "details": null }
}
```

Ví dụ `503`:

```json
{
  "success": false,
  "message": "Hệ thống tạo bài tập đang bận. Vui lòng thử lại sau.",
  "error": { "code": "LLM_UNAVAILABLE", "details": null }
}
```

Các nhóm lỗi nên xử lý: `USERNAME_ALREADY_EXISTS` (`409`), `INVALID_CREDENTIALS` (`401`), `UNAUTHORIZED` (`401`), `CHILD_NOT_FOUND` (`404`), `CHILD_FORBIDDEN` (`403`), `INVALID_INPUT` (`422`), `INVALID_MODEL_OUTPUT` (`502`), `LLM_UNAVAILABLE` (`503`), `LLM_TIMEOUT` (`504`). Mã lỗi dùng tiếng Anh như định danh kỹ thuật; **thông báo cho người dùng luôn là tiếng Việt**.

## 7. Hợp đồng BE ↔ LLM Server – GỢI Ý

### 7.1. Text generation API

`POST /internal/llm/generate` (chỉ BE được gọi; cần hạn chế truy cập nội bộ hoặc secret giữa các dịch vụ).

**Request sinh câu hỏi:**

```json
{
  "task": "Sinh câu hỏi trắc nghiệm",
  "model": "Mô hình tạo nội dung mặc định",
  "prompt": "Hãy tạo 2 câu hỏi trắc nghiệm một đáp án về động vật và thực vật cho trẻ 7 tuổi, mức cơ bản. Trả về JSON đúng cấu trúc được yêu cầu.",
  "temperature": 0.5,
  "max_output_tokens": 1800
}
```

`model` là nhãn logic ví dụ bằng tiếng Việt; khi triển khai có thể dùng mã model thực của nhà cung cấp do cấu hình LLM Server ánh xạ. Response:

```json
{
  "success": true,
  "message": "Mô hình đã tạo nội dung",
  "data": {
    "content": "{\"questions\":[{\"question_id\":\"cau-01\",\"content\":\"Con vật nào sống dưới nước?\",\"options\":[{\"option_id\":\"A\",\"text\":\"Con cá\"},{\"option_id\":\"B\",\"text\":\"Con gà\"}],\"correct_option_ids\":[\"A\"],\"explanation\":\"Cá sống dưới nước.\"}]}"
  }
}
```

Có thể tốt hơn nếu LLM Server trả **`data.output` là JSON object thay vì chuỗi `content`**, miễn hai bên thống nhất. **EGM là nơi kiểm tra Pydantic** sau khi nhận; LLM Server chỉ cần đảm bảo xử lý nhà cung cấp và truyền kết quả nhất quán.

### 7.2. Vision API (tương lai)

`POST /internal/llm/vision`: input ảnh (multipart hoặc ảnh tham chiếu lưu trữ an toàn) + prompt đánh giá; output text/JSON theo cùng envelope. Có thể thêm `POST /internal/llm/image-generate` nếu phát triển hoàn thiện tranh. Không phải mọi text model đều có khả năng vision; cấu hình chọn model phải dựa vào khả năng thực tế.

## 8. Prompt mẫu tiếng Việt cho Exercise Generation Module

> Các prompt dưới đây là **mẫu gợi ý**, không phải prompt cố định. Prompt phải bao gồm yêu cầu nội dung và yêu cầu JSON rõ ràng; khi triển khai nên dùng structured output/schema nếu model hỗ trợ và **vẫn kiểm tra ở BE**. Không nên nhồi toàn bộ dữ liệu cá nhân của trẻ vào prompt; chỉ đưa độ tuổi và sở thích khi thực sự cần cá nhân hóa.

### 8.1. Prompt sinh trắc nghiệm một đáp án

```text
Bạn là trợ lý giáo dục thân thiện dành cho trẻ em Việt Nam.
Hãy tạo {question_count} câu hỏi trắc nghiệm một đáp án đúng.
Môn học: {subject}.
Chủ đề: {topic}.
Mức độ: {level} (chỉ dùng Cơ bản hoặc Nâng cao).
Độ tuổi người học: {age}.
Yêu cầu:
- Nội dung chính xác, an toàn, dễ hiểu, phù hợp lứa tuổi và chủ đề.
- Mỗi câu có 3–4 phương án, đúng duy nhất một phương án.
- Các lựa chọn không trùng nghĩa, không chứa đáp án mơ hồ.
- Có giải thích ngắn, tích cực, bằng tiếng Việt.
- Trả về DUY NHẤT JSON hợp lệ, không Markdown, không lời dẫn.
- Key JSON dùng tiếng Anh: questions, question_id, content, options,
  option_id, text, correct_option_ids, explanation.
- Toàn bộ nội dung chuỗi cho trẻ đọc bằng tiếng Việt.
- correct_option_ids là mảng chứa đúng một option_id hợp lệ.
```

### 8.2. Prompt sinh trắc nghiệm nhiều đáp án

```text
Bạn là trợ lý giáo dục dành cho trẻ em Việt Nam.
Tạo {question_count} câu hỏi trắc nghiệm có nhiều đáp án đúng.
Môn học: {subject}; Chủ đề: {topic}; Mức độ: {level}; Tuổi: {age}.
Mỗi câu có 4–5 phương án và từ 2 đến 3 phương án đúng.
Số đáp án đúng có thể khác nhau giữa các câu; không cần báo trước cho trẻ.
Các lựa chọn phải độc lập, rõ ràng; giải thích vì sao đáp án đúng.
Trả về DUY NHẤT JSON hợp lệ theo schema câu hỏi trắc nghiệm đã thống nhất.
Key JSON tiếng Anh; câu hỏi, lựa chọn, giải thích hoàn toàn bằng tiếng Việt.
correct_option_ids chứa đầy đủ ID các phương án đúng, không trùng nhau.
```

### 8.3. Prompt sinh câu trả lời mở

```text
Bạn là trợ lý giáo dục dành cho trẻ em Việt Nam.
Tạo {question_count} câu hỏi mở cho trẻ {age} tuổi.
Môn học: {subject}; Chủ đề: {topic}; Mức độ: {level}.
Câu hỏi chỉ cần trả lời bằng từ, cụm từ, danh sách hoặc 1–3 câu ngắn.
Ưu tiên những câu hỏi có thể chấp nhận nhiều cách trả lời đúng.
Tránh câu hỏi quá mơ hồ hoặc yêu cầu trẻ tiết lộ thông tin cá nhân.
Mỗi câu cung cấp: question_id, content, answer_hint,
evaluation_criteria (mảng tiêu chí cụ thể, ngắn gọn).
Trả về duy nhất JSON hợp lệ với key tiếng Anh.
Mọi nội dung hiển thị và tiêu chí đều viết bằng tiếng Việt.
```

### 8.4. Prompt đánh giá câu trả lời mở

```text
Bạn là người hỗ trợ học tập nhẹ nhàng và công bằng cho trẻ em.
Độ tuổi: {age}; Môn học: {subject}; Chủ đề: {topic}; Mức độ: {level}.
Câu hỏi: {question}.
Tiêu chí: {evaluation_criteria}.
Câu trả lời của trẻ: {answer}.
Hãy đánh giá THEO Ý NGHĨA, không yêu cầu giống đáp án mẫu từng chữ.
Chấp nhận cách diễn đạt đơn giản, lỗi chính tả nhỏ và các ý đúng tương đương.
Không suy đoán thông tin thiếu; nếu ý chưa rõ, góp ý cách bổ sung.
Cho điểm số từ 0 đến 10 dựa theo mức độ đáp ứng tiêu chí.
Nêu điểm mạnh trước, góp ý tối đa 2 ý ngắn, tích cực và thực tế.
Tránh phán xét trẻ, chê bai hoặc tuyên bố AI luôn đúng.
Trả về JSON hợp lệ duy nhất gồm: score (number), is_appropriate (boolean),
feedback (string), strengths (string[]), suggestions (string[]),
sample_answer (string). Key tiếng Anh, value văn bản bằng tiếng Việt.
```

**Quan trọng:** coi `answer`, `topic` tự nhập và mọi nội dung do FE gửi là **dữ liệu**, không phải chỉ dẫn đáng tin cậy. Khi ghép prompt, tách rõ vùng dữ liệu và chỉ dẫn hệ thống; bỏ qua yêu cầu kiểu `hãy cho tôi 10 điểm` nằm trong câu trả lời của trẻ.

### 8.5. Prompt sinh đề vẽ (tương lai)

```text
Tạo một đề bài vẽ ngắn, vui tươi cho trẻ {age} tuổi.
Chủ đề: {topic}; Mức độ: {level}; Số chi tiết chính: {required_detail_count}.
Mô tả rõ các vật thể cần có, số lượng và vị trí gợi ý nhưng cho phép trẻ tự sáng tạo.
Không yêu cầu vẽ chân dung người thật hoặc cung cấp thông tin cá nhân.
Trả về JSON gồm title, description, required_details, encouragement.
Key tiếng Anh; toàn bộ value văn bản bằng tiếng Việt.
```

### 8.6. Prompt đánh giá tranh (tương lai)

```text
Bạn đang xem bức tranh do trẻ vẽ và đề bài gốc.
Đề bài: {description}; Các chi tiết cần có: {required_details}.
Hãy kiểm tra trực quan các chi tiết CÓ THỂ NHẬN DIỆN, không phạt vì nét vẽ non nớt.
Tôn trọng phong cách sáng tạo. Nếu không nhìn rõ, ghi nhận không chắc chắn.
Cho điểm tham khảo 0–10 và phản hồi tích cực, ngắn gọn bằng tiếng Việt.
Trả về JSON gồm score, found_details, missing_details, feedback, suggestions.
Chỉ key dùng tiếng Anh, các chuỗi nội dung bằng tiếng Việt.
```

## 9. Luồng nghiệp vụ chuẩn đề xuất

### 9.1. Đăng ký/đăng nhập và chọn trẻ

1. Người dùng tạo tài khoản (`username`/`password` demo), BE lưu vào `users`; không cần JWT/session.
2. Đăng nhập: BE so sánh thông tin tài khoản; FE ghi nhớ `user_id` từ response và chuyển sang danh sách hồ sơ trẻ.
3. Nếu chưa có hồ sơ: FE mở form `Tạo hồ sơ cho bé`. Nếu có: chọn hồ sơ đang học.
4. Người dùng có thể xem, sửa hoặc xóa hồ sơ theo `user_id`. Đăng xuất chỉ xóa `user_id` đang ghi nhớ trên FE.

### 9.2. Module 1 – Trắc nghiệm FE tự chấm

1. FE chọn `child_id`, môn học → chủ đề → mức độ → dạng bài → số câu (1–5).
2. FE gửi `/api/exercises/quiz/generate`; BE kiểm tra quyền với `child_id`, input và độ tuổi.
3. EGM xây prompt → LLM Server → model; EGM parse/validate Pydantic, chuẩn hóa response.
4. FE render theo `question_type`, lưu lựa chọn từng câu. Không gọi LLM mỗi khi người học chọn đáp án.
5. Bấm `Nộp bài` → FE so sánh tập ID, tính điểm thang 10, hiển thị giải thích và nút luyện lại.

### 9.3. Module 2 – Câu trả lời mở

1. FE chọn cấu hình tương tự Module 1 và gọi `/api/exercises/open/generate`.
2. BE/EGM gọi model sinh câu hỏi và trả `questions` + `evaluation_criteria`.
3. Trẻ nhập câu trả lời; FE gọi `/api/exercises/open/evaluate` cho câu đó.
4. EGM tạo prompt đánh giá dựa trên câu hỏi gốc, câu trả lời và tiêu chí; LLM Server gọi model.
5. BE kiểm tra schema điểm/nhận xét, trả kết quả; FE hiển thị nhận xét và gợi ý. Không coi điểm AI là kết luận tuyệt đối.

### 9.4. Module 3 – Bài tập vẽ (sau MVP)

1. FE chọn chủ đề, mức độ và tùy chọn số chi tiết; BE/EGM sinh đề vẽ.
2. FE hiển thị mô tả và canvas; trẻ vẽ, có thể xem trước và gửi ảnh.
3. BE kiểm tra ảnh, gọi model vision cùng đề bài và các chi tiết bắt buộc.
4. FE hiển thị điểm tham khảo và góp ý; nếu làm thêm image generation thì hiển thị 2 ảnh cạnh nhau và đánh dấu nguồn gốc rõ ràng.

## 10. Quy tắc tích hợp và kiểm thử prototype

### 10.1. Những điểm nhóm cần chốt trước khi code tích hợp

| Quyết định | Đề xuất mặc định | Có thể đổi không? |
|---|---|---|
| Một tài khoản bao nhiêu hồ sơ trẻ | N hồ sơ, dùng `child_id` | Có, nhưng phải sửa API / UI nhất quán |
| Cách nhận diện người dùng | Gửi `user_id` trong request; FE giữ ID người dùng sau đăng nhập | Có, prototype không dùng JWT/session |
| Tên endpoint và key JSON | Theo mục 6 | Có, nếu cập nhật tài liệu contract cùng lúc |
| Giá trị `question_type`, `subject`, `level` | Chuỗi tiếng Việt | Có, nếu map nhãn UI nhất quán |
| Chấm Module 1 | FE tự chấm, đúng toàn phần | Có, nhưng không bắt buộc gọi BE |
| Chấm Module 2 | Gửi từng câu qua BE → LLM | Có thể thêm batch |
| Lưu lịch sử bài | Không trong MVP | Có |
| Điểm số | 0–10 | Có, nếu FE/BE chốt cùng một thang |
| Số câu | 1–5 | Nên giữ cho bản demo |
| Model AI | Nhóm LLM Server tự chọn | Có, cần ghi lại model và giới hạn |

### 10.2. Test tối thiểu

| STT | Tình huống | Kết quả mong đợi |
|---|---|---|
| 1 | Đăng ký username mới | `201`, thông báo tiếng Việt, DB lưu tài khoản demo |
| 2 | Đăng ký trùng username | `409`, không tạo tài khoản trùng |
| 3 | Đăng nhập sai mật khẩu | `401`, thông báo tên đăng nhập hoặc mật khẩu không đúng |
| 4 | Tạo hồ sơ thiếu tên / tuổi không hợp lệ | `422` và mô tả lỗi |
| 5 | Gửi `child_id` không thuộc `user_id` | `404` hoặc `400`, tránh sửa nhầm hồ sơ |
| 6 | Sinh trắc nghiệm 0 hoặc 6 câu | `422` |
| 7 | Module 1 một đáp án, chọn đúng | FE ghi đúng, không request chấm BE |
| 8 | Module 1 nhiều đáp án, chọn thiếu/thừa | FE ghi sai nếu dùng quy tắc đúng toàn phần |
| 9 | Output LLM có đáp án trỏ tới option không tồn tại | BE không trả bài lỗi cho FE; retry giới hạn hoặc `502` |
| 10 | Câu mở có ý đúng nhưng khác diễn đạt | LLM nhận diện ý nghĩa, phản hồi tích cực |
| 11 | Câu trả lời mở rỗng | `422`, thông báo tiếng Việt |
| 12 | LLM timeout hoặc rate limit | FE nhận lỗi thân thiện, có thể bấm `Thử lại` |
| 13 | Chủ đề tự nhập có chỉ dẫn độc hại | EGM coi là dữ liệu, không thực thi chỉ dẫn |
| 14 | Tất cả JSON trả cho FE | Key tiếng Anh, nội dung hiển thị tiếng Việt, schema hợp lệ |

### 10.3. Giới hạn của bản thử nghiệm

- **Không làm các hạng mục production**: JWT, refresh token, session, phân quyền vai trò, email verification, quản lý người dùng phức tạp, bảng audit, cơ chế chống tấn công nhiều lớp.
- Chỉ dùng tài khoản và hồ sơ trẻ **giả**; không dùng mật khẩu thật. Vì request chỉ chứa `user_id`, bất kỳ ai gọi được API đều có thể giả mạo ID người dùng. Do đó không đưa prototype lên môi trường công khai hoặc sử dụng dữ liệu nhạy cảm.
- API key của nhà cung cấp LLM vẫn cần đặt trong `.env` phía server, không nhúng vào frontend hoặc commit lên Git; đây là yêu cầu vận hành để tránh mất quota/chi phí, không phải xây dựng hệ thống bảo mật.
- Chỉ giữ các xử lý thực sự giúp **đánh giá LLM**: kiểm tra JSON/Pydantic, số câu 1–5, xử lý timeout, đầu ra thiếu trường, phản hồi tiếng Việt, tránh nội dung không phù hợp với trẻ.
- Khi sau này muốn đưa ra người dùng thật, **phải thiết kế lại cơ chế xác thực, bảo vệ dữ liệu trẻ em và giới hạn truy cập**; bản demo này không phải nền tảng đủ an toàn để triển khai production.

## 11. Phân công 4 thành viên – sửa trùng số thứ tự trong tài liệu gốc

| Thành viên | Phụ trách chính | Sản phẩm bàn giao |
|---|---|---|
| **Người 1 – Đắc Quang** | **Web Frontend:** auth, hồ sơ trẻ, cấu hình bài, render theo `question_type`, chấm Module 1, gửi chấm Module 2, UX loading/error | FE source, `package.json`, `.env.example`, mô tả UI/State, API client, hướng dẫn chạy |
| **Người 2 – Minh Quân** | **Backend quản lý tài khoản/hồ sơ + Module 1:** DB, auth, API children, prompt/validate trắc nghiệm, EGM Module 1, phối hợp tích hợp | BE phần được giao, migrations/DDL, Pydantic schema, test, API docs, hướng dẫn chạy |
| **Người 3 – Duy Thanh** | **Backend Module 2:** sinh câu hỏi mở, chấm câu trả lời, prompt riêng cho hai tác vụ, validate output, tích hợp LLM Server | Router/service Module 2, Pydantic schema, API docs, test, hướng dẫn chạy |
| **Người 4 – Hoàng Tùng** | **LLM Server:** adapter/provider, model configuration, API nội bộ, retry/timeout/rate limit, thống nhất response, hỗ trợ vision sau MVP | LLM Server source, `.env.example`, `requirements.txt`, API contract, model list, hướng dẫn chạy |

**Chỗ giao nhau cần xác định:** Người 2 và 3 cùng đóng góp vào **một Backend API**, nên cần thống nhất ownership của `main.py`, kết nối DB, helper gọi LLM, exception handler và response envelope. Người 4 chỉ quản lý cách **gọi model**, không phải người duy nhất quyết định prompt nội dung. Người 1 làm FE dựa trên contract đã thống nhất, có thể mock JSON trước khi BE xong.

### 11.1. Thứ tự phối hợp đề xuất

1. Cả nhóm thống nhất endpoint, schema câu hỏi, mã lỗi, cách gửi `user_id` và mẫu response; lưu `api-contract.md`.
2. Người 1 làm màn hình với mock JSON; Người 2 làm auth/children + Module 1; Người 3 làm Module 2 với stub LLM; Người 4 tạo LLM Server mock/call thật.
3. Ghép luồng BE ↔ LLM Server, sau đó FE ↔ BE; kiểm thử các lỗi/timeout/schema và demo tối đa 5 câu.
4. Module 3 chỉ triển khai nếu các tính năng MVP ổn định và đủ thời gian.

## 12. Quy cách tài liệu bàn giao của mỗi người

Mỗi thành viên nên có một file Markdown hoặc DOCX riêng gồm: **(1)** mục tiêu/phạm vi; **(2)** công nghệ/phiên bản; **(3)** cấu trúc thư mục và trách nhiệm file; **(4)** luồng xử lý; **(5)** endpoint/request/response hoặc component/state liên quan; **(6)** cấu hình `.env.example`, `requirements.txt`/`package.json`; **(7)** cách cài đặt/chạy và test; **(8)** lỗi thường gặp/giải pháp; **(9)** các quyết định đã thay đổi so với tài liệu gợi ý và lý do.

**Định nghĩa hoàn thành bản thử nghiệm:** có thể đăng ký/đăng nhập, tạo/chọn hồ sơ trẻ, chọn môn/chủ đề/mức độ/dạng/số câu, sinh câu hỏi bằng model, tự chấm trắc nghiệm trên FE, gửi chấm câu mở qua LLM, hiện điểm/nhận xét tiếng Việt và xử lý được các trường hợp lỗi cơ bản. **Không cần** lịch sử, bảng xếp hạng, dashboard, bài vẽ hay model thứ ba để nghiệm thu MVP.

---

**Ghi chú về nguồn:** Tài liệu này dựa trên nội dung gốc *“Phân tích và thiết kế chi tiết hệ thống LearnMate AI – AI Learning Companion for Kids”*. Những phần có tiêu đề **đề xuất/gợi ý/tương lai** (schema, endpoint mở rộng, định danh bằng user_id, SQL, prompt, kiểm thử) là phần được bổ sung để nhóm có căn cứ triển khai, không phải yêu cầu đã được tài liệu gốc quyết định sẵn.

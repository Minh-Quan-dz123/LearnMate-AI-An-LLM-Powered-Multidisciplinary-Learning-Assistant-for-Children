# LearnMate AI — Backend

## 1. Giới thiệu

LearnMate AI là dự án thử nghiệm khả năng ứng dụng LLM trong việc sinh bài tập và đánh giá câu trả lời dành cho trẻ em.

Backend được xây dựng bằng Python và FastAPI, có nhiệm vụ cung cấp REST API cho Frontend, quản lý dữ liệu người dùng, xây dựng prompt và giao tiếp với LLM Server.

Đây là project thử nghiệm, không phải hệ thống production. Do đó thiết kế được giữ đơn giản, ưu tiên tính dễ hiểu và khả năng tích hợp.

## 2. Công nghệ

- Python
- FastAPI
- Pydantic
- Supabase (PostgreSQL)
- HTTPX (gọi LLM Server)
- Uvicorn

## 3. Các thành phần chính

Backend gồm hai module nghiệp vụ:

**Module 1 — Trắc nghiệm**

- Sinh bài tập trắc nghiệm một đáp án.
- Sinh bài tập trắc nghiệm nhiều đáp án.
- Trả về câu hỏi, các lựa chọn, đáp án đúng và giải thích.
- Frontend tự kiểm tra đáp án, Backend không chấm điểm.

**Module 2 — Câu hỏi mở**

- Sinh câu hỏi cần nhập câu trả lời.
- Nhận câu trả lời từ Frontend.
- Gửi câu hỏi và câu trả lời đến LLM để đánh giá.
- Trả về điểm số và nhận xét cho Frontend.

Ngoài ra, Backend còn quản lý tài khoản và hồ sơ trẻ.

## 4. Cấu trúc project

learnmate_backend/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── constants.py
│   ├── llm_client.py
│   ├── database.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── children.py
│   │   ├── module1.py
│   │   └── module2.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── children.py
│   │   ├── module1.py
│   │   └── module2.py
│   │
│   └── egm/
│       ├── __init__.py
│       ├── module1_egm.py
│       └── module2_egm.py
│
├── docs/
│   ├── module1.md
│   └── module2.md
│
└── scripts/
    └── try_llm.py

## 5. Chức năng từng file

### 5.1. Các file chung trong app/

| File          | Chức năng                                                       |
| ------------- | --------------------------------------------------------------- |
| main.py       | Khởi tạo FastAPI và đăng ký các router                          |
| config.py     | Đọc cấu hình từ .env                                            |
| constants.py  | Lưu danh sách môn học, chủ đề, độ khó và các hằng số dùng chung |
| database.py   | Khởi tạo kết nối Supabase                                       |
| llm_client.py | Gửi HTTP request đến LLM Server và nhận response                |
| __init__.py   | Đánh dấu thư mục là Python package                              |

### 5.2. Thư mục routers/

Chứa các API endpoint mà Frontend gọi đến.

| File        | Chức năng                                   |
| ----------- | ------------------------------------------- |
| auth.py     | Đăng ký và đăng nhập                        |
| children.py | Tạo, xem, cập nhật, xóa hồ sơ trẻ           |
| module1.py  | API sinh bài tập trắc nghiệm                |
| module2.py  | API sinh câu hỏi mở và đánh giá câu trả lời |

Router chủ yếu nhận request, kiểm tra dữ liệu thông qua Pydantic và gọi hàm xử lý nghiệp vụ tương ứng.

### 5.3. Thư mục schemas/

Định nghĩa cấu trúc dữ liệu bằng Pydantic.

| File        | Chức năng                                   |
| ----------- | ------------------------------------------- |
| auth.py     | Dữ liệu đăng ký, đăng nhập                  |
| children.py | Dữ liệu tạo và cập nhật hồ sơ trẻ           |
| module1.py  | Request/response của bài tập trắc nghiệm    |
| module2.py  | Request/response của câu hỏi mở và đánh giá |

### 5.4. Thư mục egm/

EGM viết tắt của Exercise Generation Module.

Đây là nơi xây dựng prompt và xử lý dữ liệu bài tập.

**module1_egm.py**

- Tạo prompt sinh trắc nghiệm.
- Gọi LLM Server thông qua llm_client.
- Chuẩn hóa dữ liệu bài tập.

**module2_egm.py**

- Tạo prompt sinh câu hỏi mở.
- Tạo prompt đánh giá câu trả lời.
- Gọi LLM Server.
- Chuẩn hóa kết quả đánh giá.

## 6. Luồng xử lý

### Module 1

Frontend → routers/module1.py → egm/module1_egm.py → llm_client.py → LLM Server

Khi LLM trả kết quả:

LLM Server → EGM → Router → Frontend

Frontend tự chấm bài dựa trên đáp án Backend trả về.

### Module 2

**Sinh câu hỏi:**

Frontend → routers/module2.py → egm/module2_egm.py → llm_client.py → LLM Server

**Chấm câu trả lời:**

Frontend gửi câu hỏi và câu trả lời → Backend xây dựng prompt đánh giá → LLM Server → Backend → Frontend.

## 7. Quy ước dữ liệu

- Tên key trong JSON sử dụng tiếng Anh.
- Các giá trị nội dung nghiệp vụ sử dụng tiếng Việt.
- Các giá trị kỹ thuật như ID, URL, mã lựa chọn và tên model có thể sử dụng định dạng phù hợp.
- Sử dụng `user_id` để xác định người dùng trong các request cần thiết.
- Không triển khai JWT hoặc phân quyền trong phiên bản thử nghiệm.
- Module 1 không cần lưu bài tập hay đáp án vào Database.
- Module 2 không bắt buộc lưu lịch sử đánh giá.
- Module 3 (bài tập vẽ) chưa triển khai.

## 8. Quy ước response

Đề xuất cấu trúc chung:

{
  "success": true,
  "message": "Thao tác thành công",
  "data": {}
}

Khi có lỗi:

{
  "success": false,
  "message": "Dữ liệu không hợp lệ"
}

Đây là cấu trúc gợi ý. Các thành viên cần thống nhất trước khi tích hợp.

## 9. Phân công

### Quân

- main.py
- config.py
- database.py
- routers/auth.py
- routers/children.py
- routers/module1.py
- schemas/auth.py
- schemas/children.py
- schemas/module1.py
- egm/module1_egm.py
- docs/module1.md

### Thành viên phụ trách Module 2

- routers/module2.py
- schemas/module2.py
- egm/module2_egm.py
- docs/module2.md
- llm_client.py (theo phân công đã thống nhất)

Các file chung như constants.py, README.md, requirements.txt cần được thống nhất khi sửa đổi.

## 10. Hướng dẫn chạy

### Tạo môi trường

py -m venv .venv
.\.venv\Scripts\Activate.ps1

### Cài thư viện

pip install -r requirements.txt

### Cấu hình

Sao chép .env.example thành .env và điền thông tin kết nối.

### Khởi động

python -m uvicorn app.main:app --reload

Truy cập:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## 11. Quy ước phối hợp

1. Mỗi thành viên phụ trách phần code được phân công.
2. Trước khi thay đổi file chung, cần thông báo cho người còn lại.
3. Khi thêm hoặc sửa API, cần thống nhất request và response với Frontend.
4. Khi thay đổi hàm quan trọng hoặc luồng nghiệp vụ, cập nhật file docs tương ứng.
5. Không push file .env hoặc môi trường .venv.
6. Không tự ý thay đổi cấu trúc JSON chung khi chưa trao đổi.
7. Ưu tiên code đơn giản, dễ đọc và dễ kiểm thử.

## 12. Ghi chú

Các mô tả trong tài liệu chỉ mang tính định hướng triển khai. Lập trình viên có thể điều chỉnh thiết kế nội bộ nếu thấy hợp lý, miễn là các thành phần giao tiếp được với nhau theo hợp đồng đã thống nhất.
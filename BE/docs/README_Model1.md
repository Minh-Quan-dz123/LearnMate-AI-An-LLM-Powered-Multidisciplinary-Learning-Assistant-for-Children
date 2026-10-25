# Module 1 — Backend

**Người phụ trách:** Quân

## 1. Phạm vi

Phụ trách ba nhóm chức năng:

- Quản lý tài khoản.
- Quản lý hồ sơ trẻ.
- Sinh bài tập trắc nghiệm.

## 2. Database

Dự kiến sử dụng hai bảng.

### Bảng users

| Trường   | Kiểu dữ liệu    | Ý nghĩa                 |
| -------- | --------------- | ----------------------- |
| id       | BIGINT, PK      | ID người dùng, tự tăng  |
| username | VARCHAR, UNIQUE | Tên đăng nhập           |
| password | TEXT            | Mật khẩu tài khoản demo |

### Bảng child_profiles

| Trường    | Kiểu dữ liệu | Ý nghĩa             |
| --------- | ------------ | ------------------- |
| id        | BIGINT, PK   | ID hồ sơ trẻ        |
| user_id   | BIGINT, FK   | Tham chiếu users.id |
| name      | VARCHAR      | Tên hoặc biệt danh  |
| age       | INTEGER      | Tuổi                |
| gender    | VARCHAR      | Giới tính           |
| interests | JSONB        | Danh sách sở thích  |

Mỗi user dự kiến có một hồ sơ trẻ. Đặt UNIQUE cho child_profiles.user_id nếu áp dụng quy ước này.

Dữ liệu sử dụng trong project chỉ là dữ liệu demo.

## 3. Các file và hàm dự kiến

### app/database.py

**get_supabase()**

- Đọc thông tin kết nối.
- Khởi tạo hoặc trả về Supabase client.
- Được các router sử dụng khi thao tác Database.

### app/routers/auth.py

**register()**

- Nhận username và password.
- Kiểm tra username đã tồn tại chưa.
- Tạo user.
- Trả về user_id.

**login()**

- Nhận username và password.
- Kiểm tra thông tin đăng nhập.
- Trả về user_id và username nếu hợp lệ.

### app/routers/children.py

**create_child()**

- Nhận user_id và thông tin trẻ.
- Kiểm tra user tồn tại.
- Tạo hồ sơ trẻ.

**get_child()**

- Nhận user_id.
- Lấy hồ sơ trẻ theo user_id.

**update_child()**

- Nhận user_id và dữ liệu cập nhật.
- Cập nhật hồ sơ trẻ.

**delete_child()**

- Nhận user_id.
- Xóa hồ sơ trẻ.

### app/routers/module1.py

**generate_quiz()**

- Nhận yêu cầu sinh bài tập từ Frontend.
- Kiểm tra dữ liệu đầu vào bằng Pydantic.
- Gọi module1_egm.generate_questions().
- Trả về danh sách câu hỏi.

### app/egm/module1_egm.py

**build_generation_prompt()**

- Nhận môn học, chủ đề, độ khó, dạng bài và số câu hỏi.
- Tạo prompt tiếng Việt để yêu cầu LLM sinh bài tập đúng định dạng.

**generate_questions()**

- Tạo prompt.
- Gọi llm_client.
- Kiểm tra dữ liệu LLM trả về.
- Trả về JSON bài tập.

Tên hàm và tham số là gợi ý, có thể điều chỉnh trong quá trình code.

## 4. API dự kiến

| Method | Endpoint                | Chức năng            |
| ------ | ----------------------- | -------------------- |
| POST   | /api/auth/register      | Đăng ký              |
| POST   | /api/auth/login         | Đăng nhập            |
| POST   | /api/children           | Tạo hồ sơ            |
| GET    | /api/children/{user_id} | Xem hồ sơ            |
| PUT    | /api/children/{user_id} | Cập nhật hồ sơ       |
| DELETE | /api/children/{user_id} | Xóa hồ sơ            |
| POST   | /api/module1/generate   | Sinh bài trắc nghiệm |

### Ví dụ request sinh bài

{
  "user_id": 1,
  "subject": "Khoa học tự nhiên",
  "topic": "Động vật và thực vật",
  "level": "Cơ bản",
  "question_type": "Trắc nghiệm một đáp án",
  "question_count": 3
}

### Response dự kiến

{
  "success": true,
  "message": "Sinh bài tập thành công",
  "data": {
    "questions": [
      {
        "id": 1,
        "question": "Động vật nào sau đây có thể bay?",
        "question_type": "Trắc nghiệm một đáp án",
        "options": [
          {"id": "A", "text": "Con mèo"},
          {"id": "B", "text": "Con chim"},
          {"id": "C", "text": "Con cá"}
        ],
        "correct_answers": ["B"],
        "explanation": "Chim có cánh và nhiều loài chim có thể bay."
      }
    ]
  }
}

Với trắc nghiệm nhiều đáp án, correct_answers có thể chứa nhiều ID.

## 5. Prompt mẫu

Bạn là giáo viên thân thiện với trẻ em.

Hãy tạo bài tập trắc nghiệm bằng tiếng Việt theo các thông tin:

- Môn học: {subject}
- Chủ đề: {topic}
- Độ khó: {level}
- Dạng bài: {question_type}
- Số câu: {question_count}
- Tuổi trẻ: {age}

Yêu cầu:

1. Nội dung phù hợp độ tuổi.
2. Câu hỏi rõ ràng, dễ hiểu.
3. Nếu trắc nghiệm một đáp án, mỗi câu chỉ có một đáp án đúng.
4. Nếu trắc nghiệm nhiều đáp án, có thể có từ hai đáp án đúng trở lên.
5. Mỗi câu có ít nhất ba lựa chọn.
6. Có giải thích ngắn gọn cho đáp án đúng.
7. Trả về JSON theo schema được cung cấp.
8. Không thêm văn bản ngoài JSON.

## 6. Luồng xử lý

1. FE gửi request sinh bài.
2. Router kiểm tra request.
3. EGM xây dựng prompt.
4. EGM sử dụng llm_client gọi LLM Server.
5. LLM Server trả về dữ liệu.
6. EGM kiểm tra và chuẩn hóa JSON.
7. Router trả kết quả về FE.
8. FE hiển thị bài tập và tự chấm.

## 7. Danh sách công việc

- Kết nối Supabase.
- Tạo hai bảng Database.
- Viết schemas/auth.py.
- Viết routers/auth.py.
- Viết schemas/children.py.
- Viết routers/children.py.
- Viết schemas/module1.py.
- Viết prompt cho Module 1.
- Viết API sinh bài.
- Kiểm thử API.
- Cập nhật tài liệu khi hoàn thiện.

## 8. Ghi chú

- Không JWT hoặc session.
- user_id chỉ dùng để xác định bản ghi trong prototype.
- Không lưu bài làm trắc nghiệm.
- Không cần API chấm trắc nghiệm.
- Ưu tiên triển khai chức năng chạy được trước, sau đó mới cải thiện prompt.
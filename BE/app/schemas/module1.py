# ============================================================
# FILE: app/schemas/module1.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Định nghĩa cấu trúc Request và Response
# cho Module 1 - Bài tập trắc nghiệm.
#
# Hỗ trợ:
# - Trắc nghiệm một đáp án.
# - Trắc nghiệm nhiều đáp án.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel
# - pydantic.Field
# - pydantic.model_validator
# - app.constants:
#     Sử dụng các giá trị question_type, level và giới hạn số câu.


# 2. CLASS QuizGenerateRequest
#
# Dữ liệu FE gửi lên:
#
# - child_id: int
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - question_count: int
#
# TODO:
# - Kiểm tra child_id hợp lệ.
# - Kiểm tra subject và topic không rỗng.
# - Kiểm tra level là "Cơ bản" hoặc "Nâng cao".
# - Kiểm tra question_type là một trong hai loại trắc nghiệm.
# - Kiểm tra question_count trong khoảng 1 đến 5.
#
# Lưu ý:
# Tuổi được lấy từ Child Profile trong Database,
# không yêu cầu FE tự truyền tuổi.


# 3. CLASS QuizOption
#
# Đại diện cho một lựa chọn.
#
# Các trường:
# - option_id: str
# - text: str
#
# Ví dụ:
# {
#   "option_id": "A",
#   "text": "Con mèo"
# }


# 4. CLASS QuizQuestion
#
# Đại diện cho một câu hỏi trắc nghiệm.
#
# Các trường:
# - question_id: str
# - content: str
# - options: list[QuizOption]
# - correct_option_ids: list[str]
# - explanation: str
#
# TODO:
# - Kiểm tra nội dung câu hỏi không rỗng.
# - Kiểm tra danh sách options không rỗng.
# - Kiểm tra option_id không trùng nhau.
# - Kiểm tra correct_option_ids không trùng nhau.
# - Kiểm tra tất cả đáp án đúng tồn tại trong options.
# - Kiểm tra explanation không rỗng.
#
# Lưu ý:
# Điều kiện đúng 1 hoặc nhiều đáp án phụ thuộc question_type.
# Có thể thực hiện kiểm tra này trong EGM khi đã biết loại bài.


# 5. CLASS QuizData
#
# Dữ liệu bài tập trả về:
#
# - exercise_id: str
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - questions: list[QuizQuestion]
#
# TODO:
# - Đảm bảo mỗi question_id là duy nhất.
# - Đảm bảo số câu bằng question_count đã yêu cầu.
# - Đảm bảo các câu hỏi phù hợp question_type.


# 6. CLASS QuizGenerateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: QuizData
#
# Ví dụ cấu trúc:
# {
#   "success": true,
#   "message": "Tạo bài tập thành công",
#   "data": {
#     "exercise_id": "demo-bai-001",
#     "subject": "Khoa học tự nhiên",
#     "topic": "Động vật và thực vật",
#     "level": "Cơ bản",
#     "question_type": "Trắc nghiệm một đáp án",
#     "questions": []
#   }
# }
#
# questions ở ví dụ trên chỉ minh họa kiểu dữ liệu.
# Khi triển khai phải có số câu đúng theo request.


# 7. RÀNG BUỘC RIÊNG CHO QUESTION_TYPE
#
# Trắc nghiệm một đáp án:
# - Mỗi câu có đúng 1 correct_option_id.
#
# Trắc nghiệm nhiều đáp án:
# - Mỗi câu có tối thiểu 2 correct_option_ids.
#
# Các quy tắc về số phương án cần khớp prompt của EGM.


# 8. KIỂM TRA
#
# TODO:
# - question_count = 0.
# - question_count = 6.
# - Một đáp án nhưng model trả 2 đáp án đúng.
# - Đáp án đúng không tồn tại trong options.
# - Hai câu có question_id trùng nhau.
# - Model trả thiếu explanation.
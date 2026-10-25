# ============================================================
# FILE: app/schemas/module2.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Định nghĩa cấu trúc dữ liệu cho Module 2.
#
# Module 2 thực hiện:
# - Sinh câu hỏi mở.
# - Nhận câu trả lời của trẻ.
# - Trả kết quả đánh giá từ LLM.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel
# - pydantic.Field
# - pydantic.model_validator nếu cần.
# - app.constants


# 2. CLASS OpenGenerateRequest
#
# Các trường:
# - child_id: int
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - question_count: int
#
# TODO:
# - Kiểm tra child_id hợp lệ.
# - Kiểm tra dữ liệu môn học/chủ đề.
# - Kiểm tra level.
# - Chỉ chấp nhận question_type = "Câu trả lời mở".
# - Kiểm tra question_count từ 1 đến 5.


# 3. CLASS OpenQuestion
#
# Các trường:
# - question_id: str
# - content: str
# - answer_hint: str
# - evaluation_criteria: list[str]
#
# Ý nghĩa:
# question_id:
#     ID câu hỏi.
#
# content:
#     Nội dung câu hỏi cần trẻ trả lời.
#
# answer_hint:
#     Gợi ý cách trả lời.
#
# evaluation_criteria:
#     Các tiêu chí dùng để đánh giá câu trả lời.
#
# TODO:
# - Kiểm tra content không rỗng.
# - Kiểm tra danh sách tiêu chí hợp lệ.
# - Kiểm tra dữ liệu dạng string/list đúng schema.


# 4. CLASS OpenExerciseData
#
# Các trường:
# - exercise_id: str
# - question_type: str
# - questions: list[OpenQuestion]


# 5. CLASS OpenGenerateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: OpenExerciseData


# 6. CLASS OpenEvaluateRequest
#
# Dữ liệu FE gửi lên khi yêu cầu đánh giá:
#
# - child_id: int
# - question_id: str
# - question: str
# - answer: str
# - evaluation_criteria: list[str]
# - subject: str
# - topic: str
# - level: str
#
# TODO:
# - Kiểm tra các trường bắt buộc.
# - Không cho phép answer rỗng.
# - Giới hạn độ dài question, answer và topic.
# - Kiểm tra evaluation_criteria đúng kiểu dữ liệu.
# - Kiểm tra level hợp lệ.
#
# Lưu ý:
# FE gửi lại câu hỏi và tiêu chí để chấm.
# Backend không bắt buộc lưu câu hỏi vào Database.


# 7. CLASS OpenEvaluationData
#
# Các trường:
# - question_id: str
# - score: float
# - is_appropriate: bool
# - feedback: str
# - strengths: list[str]
# - suggestions: list[str]
# - sample_answer: str
#
# TODO:
# - Kiểm tra score nằm trong [0, 10].
# - Kiểm tra is_appropriate là boolean.
# - Kiểm tra các trường nhận xét đúng kiểu.
# - Giữ toàn bộ nội dung phản hồi bằng tiếng Việt.


# 8. CLASS OpenEvaluateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: OpenEvaluationData


# 9. KIỂM TRA
#
# TODO:
# - Sinh câu hỏi với question_count hợp lệ.
# - Thiếu evaluation_criteria.
# - Câu trả lời rỗng.
# - Điểm số nhỏ hơn 0 hoặc lớn hơn 10.
# - Model trả score dưới dạng chuỗi không hợp lệ.
# - Model trả thiếu feedback hoặc suggestions.
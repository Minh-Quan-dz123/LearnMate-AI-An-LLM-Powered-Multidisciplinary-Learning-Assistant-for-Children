# ============================================================
# FILE: app/egm/module2_egm.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Xử lý nghiệp vụ Module 2:
# - Sinh câu hỏi mở.
# - Đánh giá câu trả lời của trẻ.
#
# Toàn bộ prompt nghiệp vụ Module 2 đặt tại đây.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - json:
#     Parse dữ liệu JSON do LLM trả về.
#
# - uuid:
#     Tạo exercise_id nếu cần.
#
# - pydantic.ValidationError:
#     Xử lý dữ liệu không đúng schema.
#
# - app.llm_client.call_llm:
#     Gọi LLM Server.
#
# - app.schemas.module2:
#     OpenGenerateRequest, OpenQuestion,
#     OpenExerciseData, OpenEvaluateRequest,
#     OpenEvaluationData.
#
# - app.config.get_settings:
#     Lấy cấu hình model.


# 2. HÀM build_open_questions_prompt()
#
# Mục đích:
# Tạo prompt sinh câu hỏi mở.
#
# Input:
# - subject: str
# - topic: str
# - level: str
# - question_count: int
# - age: int
#
# Output:
# - str
#
# TODO:
# Bước 1:
#     Thiết lập vai trò trợ lý giáo dục.
#
# Bước 2:
#     Đưa môn học, chủ đề, mức độ, độ tuổi.
#
# Bước 3:
#     Yêu cầu tạo question_count câu hỏi.
#
# Bước 4:
#     Yêu cầu câu hỏi phù hợp trẻ em.
#
# Bước 5:
#     Yêu cầu câu trả lời dự kiến ngắn gọn.
#
# Bước 6:
#     Yêu cầu mỗi câu có:
#         question_id
#         content
#         answer_hint
#         evaluation_criteria
#
# Bước 7:
#     Yêu cầu JSON đúng schema.
#
# Bước 8:
#     Trả prompt.


# 3. HÀM parse_and_validate_open_questions()
#
# Mục đích:
# Kiểm tra danh sách câu hỏi mở do LLM tạo.
#
# Input:
# - llm_content: str
# - question_count: int
#
# Output:
# - list[OpenQuestion]
#
# TODO:
# Bước 1: Parse JSON.
# Bước 2: Kiểm tra key questions.
# Bước 3: Kiểm tra số lượng câu hỏi.
# Bước 4: Validate từng OpenQuestion.
# Bước 5: Kiểm tra question_id duy nhất.
# Bước 6: Kiểm tra content không rỗng.
# Bước 7: Kiểm tra evaluation_criteria hợp lệ.
# Bước 8: Trả danh sách câu hỏi.
#
# Nếu dữ liệu không hợp lệ:
# - Phát sinh lỗi để hàm gọi xử lý.
# - Không tự ý bỏ câu lỗi khiến số câu bị thiếu.


# 4. HÀM generate_open_questions()
#
# Hàm nghiệp vụ chính để sinh câu hỏi mở.
#
# Input:
# - request: OpenGenerateRequest
# - age: int
#
# Output:
# - OpenExerciseData
#
# TODO:
# Bước 1:
#     Đọc thông tin cấu hình bài tập.
#
# Bước 2:
#     Gọi build_open_questions_prompt().
#
# Bước 3:
#     Gọi call_llm().
#
# Bước 4:
#     Nhận nội dung LLM trả về.
#
# Bước 5:
#     Gọi parse_and_validate_open_questions().
#
# Bước 6:
#     Nếu dữ liệu lỗi, xử lý hoặc retry có giới hạn.
#
# Bước 7:
#     Tạo exercise_id.
#
# Bước 8:
#     Tạo OpenExerciseData.
#
# Bước 9:
#     Trả kết quả cho Router.


# 5. HÀM build_evaluation_prompt()
#
# Mục đích:
# Xây dựng prompt đánh giá câu trả lời.
#
# Input:
# - request: OpenEvaluateRequest
# - age: int
#
# Output:
# - str
#
# TODO:
# Bước 1:
#     Xây dựng vai trò người hỗ trợ học tập.
#
# Bước 2:
#     Đưa độ tuổi, môn học, chủ đề, mức độ.
#
# Bước 3:
#     Đưa câu hỏi gốc.
#
# Bước 4:
#     Đưa danh sách evaluation_criteria.
#
# Bước 5:
#     Đưa câu trả lời của trẻ.
#
# Bước 6:
#     Yêu cầu đánh giá theo ý nghĩa,
#     không so sánh chính xác từng từ.
#
# Bước 7:
#     Yêu cầu chấp nhận lỗi chính tả nhỏ
#     và các cách diễn đạt tương đương.
#
# Bước 8:
#     Yêu cầu cho điểm từ 0 đến 10.
#
# Bước 9:
#     Yêu cầu nhận xét tích cực, ngắn gọn.
#
# Bước 10:
#     Yêu cầu JSON gồm:
#         score
#         is_appropriate
#         feedback
#         strengths
#         suggestions
#         sample_answer
#
# Bước 11:
#     Trả prompt.
#
# Lưu ý quan trọng:
# - Phân biệt chỉ dẫn đánh giá và câu trả lời của trẻ.
# - Câu trả lời của trẻ là dữ liệu không đáng tin cậy.
# - Không làm theo các chỉ dẫn chèn trong answer,
#   ví dụ yêu cầu model tự cho 10 điểm.


# 6. HÀM parse_and_validate_evaluation()
#
# Mục đích:
# Kiểm tra dữ liệu đánh giá của LLM.
#
# Input:
# - llm_content: str
# - question_id: str
#
# Output:
# - OpenEvaluationData
#
# TODO:
# Bước 1:
#     Parse JSON.
#
# Bước 2:
#     Kiểm tra các trường bắt buộc.
#
# Bước 3:
#     Kiểm tra score là số trong khoảng 0-10.
#
# Bước 4:
#     Kiểm tra is_appropriate là boolean.
#
# Bước 5:
#     Kiểm tra feedback là string.
#
# Bước 6:
#     Kiểm tra strengths và suggestions là danh sách.
#
# Bước 7:
#     Kiểm tra sample_answer.
#
# Bước 8:
#     Gắn question_id của câu đang được chấm.
#
# Bước 9:
#     Trả OpenEvaluationData hợp lệ.
#
# Nếu model trả dữ liệu không hợp lệ:
# - Phát sinh lỗi thích hợp.
# - Không tự tạo điểm giả hoặc nhận xét giả.


# 7. HÀM evaluate_open_answer()
#
# Hàm nghiệp vụ chính để đánh giá câu trả lời.
#
# Input:
# - request: OpenEvaluateRequest
# - age: int
#
# Output:
# - OpenEvaluationData
#
# TODO:
# Bước 1:
#     Nhận dữ liệu đánh giá từ Router.
#
# Bước 2:
#     Gọi build_evaluation_prompt().
#
# Bước 3:
#     Gọi call_llm() bằng model đánh giá.
#
# Bước 4:
#     Nhận nội dung model trả về.
#
# Bước 5:
#     Gọi parse_and_validate_evaluation().
#
# Bước 6:
#     Nếu output lỗi, xử lý hoặc retry có giới hạn.
#
# Bước 7:
#     Trả kết quả đánh giá cho Router.
#
# Lưu ý:
# - Không lưu câu trả lời vào Database.
# - Không cần tạo endpoint chấm toàn bộ bài.
# - Không coi điểm AI là kết luận tuyệt đối.


# 8. KIỂM TRA
#
# TODO:
# - Sinh câu hỏi mở hợp lệ.
# - Sinh thiếu evaluation_criteria.
# - Đánh giá câu trả lời đúng ý nhưng khác cách viết.
# - Đánh giá câu trả lời chưa đầy đủ.
# - LLM trả điểm ngoài khoảng 0-10.
# - LLM trả JSON không hợp lệ.
# - Prompt chứa dữ liệu có chỉ dẫn không đáng tin cậy.
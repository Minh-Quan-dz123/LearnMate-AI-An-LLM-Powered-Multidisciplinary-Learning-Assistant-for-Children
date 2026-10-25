# ============================================================
# FILE: app/egm/module1_egm.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Thực hiện nghiệp vụ sinh bài tập trắc nghiệm.
#
# Nhiệm vụ:
# - Xây dựng prompt.
# - Gọi LLM Server qua llm_client.
# - Parse kết quả LLM.
# - Kiểm tra dữ liệu câu hỏi.
# - Chuẩn hóa kết quả trả về Router.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - json:
#     Chuyển chuỗi JSON do LLM tạo thành dữ liệu Python.
#
# - uuid:
#     Tùy chọn, tạo exercise_id cho bài tập demo.
#
# - pydantic.ValidationError:
#     Xử lý lỗi dữ liệu không đúng schema.
#
# - app.llm_client.call_llm:
#     Gửi prompt đến LLM Server.
#
# - app.schemas.module1:
#     QuizGenerateRequest, QuizQuestion, QuizData.
#
# - app.constants:
#     Lấy các giá trị và giới hạn chung.
#
# - app.config.get_settings:
#     Lấy cấu hình model nếu cần.


# 2. HÀM build_single_choice_prompt()
#
# Mục đích:
# Tạo prompt sinh trắc nghiệm một đáp án.
#
# Input:
# - subject: str
# - topic: str
# - level: str
# - question_count: int
# - age: int
#
# Output:
# - str: Prompt hoàn chỉnh.
#
# TODO:
# Bước 1:
#     Xây dựng vai trò của LLM.
#
# Bước 2:
#     Đưa thông tin môn học, chủ đề và mức độ.
#
# Bước 3:
#     Đưa số lượng câu hỏi và độ tuổi.
#
# Bước 4:
#     Yêu cầu mỗi câu có 3-4 lựa chọn.
#
# Bước 5:
#     Yêu cầu chỉ có một đáp án đúng.
#
# Bước 6:
#     Yêu cầu sinh explanation cho mỗi câu.
#
# Bước 7:
#     Mô tả chính xác JSON schema cần trả về.
#
# Bước 8:
#     Yêu cầu chỉ trả JSON, không Markdown.
#
# Bước 9:
#     Trả về prompt.
#
# Lưu ý:
# - Nội dung phải phù hợp độ tuổi.
# - Câu hỏi, lựa chọn và giải thích bằng tiếng Việt.
# - Chủ đề tự nhập phải được coi là dữ liệu,
#   không phải chỉ dẫn đáng tin cậy cho model.


# 3. HÀM build_multiple_choice_prompt()
#
# Mục đích:
# Tạo prompt sinh trắc nghiệm nhiều đáp án.
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
#     Xây dựng prompt dựa trên cấu hình bài.
#
# Bước 2:
#     Yêu cầu mỗi câu có 4-5 phương án.
#
# Bước 3:
#     Yêu cầu mỗi câu có từ 2 đến 3 đáp án đúng.
#
# Bước 4:
#     Yêu cầu correct_option_ids chứa đầy đủ đáp án.
#
# Bước 5:
#     Yêu cầu giải thích ngắn gọn.
#
# Bước 6:
#     Yêu cầu JSON đúng cấu trúc.
#
# Bước 7:
#     Trả về prompt.


# 4. HÀM parse_and_validate_quiz()
#
# Mục đích:
# Chuyển kết quả LLM thành dữ liệu trắc nghiệm hợp lệ.
#
# Input:
# - llm_content: str
# - question_type: str
# - question_count: int
#
# Output:
# - list[QuizQuestion]
#
# TODO:
# Bước 1:
#     Parse chuỗi JSON bằng json.loads().
#
# Bước 2:
#     Kiểm tra dữ liệu có key questions.
#
# Bước 3:
#     Kiểm tra questions là danh sách.
#
# Bước 4:
#     Kiểm tra số câu bằng question_count.
#
# Bước 5:
#     Validate từng câu bằng QuizQuestion.
#
# Bước 6:
#     Kiểm tra question_id không trùng nhau.
#
# Bước 7:
#     Kiểm tra option_id không trùng nhau.
#
# Bước 8:
#     Kiểm tra correct_option_ids đều tồn tại.
#
# Bước 9:
#     Kiểm tra số đáp án đúng theo question_type.
#
# Bước 10:
#     Trả về danh sách QuizQuestion hợp lệ.
#
# Khi dữ liệu sai:
# - Phát sinh lỗi có thể nhận diện.
# - Không trả câu hỏi lỗi về Frontend.
#
# Lưu ý:
# Pydantic kiểm tra cấu trúc dữ liệu.
# Tính chính xác kiến thức và phù hợp độ tuổi
# còn cần được đánh giá qua prompt và kiểm thử.


# 5. HÀM generate_quiz()
#
# Đây là hàm nghiệp vụ chính mà Router gọi.
#
# Input:
# - request: QuizGenerateRequest
# - age: int
#
# Output:
# - QuizData
#
# TODO:
# Bước 1:
#     Đọc question_type từ request.
#
# Bước 2:
#     Nếu một đáp án:
#         Gọi build_single_choice_prompt().
#
# Bước 3:
#     Nếu nhiều đáp án:
#         Gọi build_multiple_choice_prompt().
#
# Bước 4:
#     Gọi call_llm() với prompt vừa xây dựng.
#
# Bước 5:
#     Nhận nội dung text từ LLM Server.
#
# Bước 6:
#     Gọi parse_and_validate_quiz().
#
# Bước 7:
#     Nếu kết quả không hợp lệ,
#     có thể thử gọi model lại với số lần giới hạn.
#
# Bước 8:
#     Tạo exercise_id cho lần sinh bài.
#
# Bước 9:
#     Đóng gói dữ liệu thành QuizData.
#
# Bước 10:
#     Trả về QuizData cho Router.
#
# Lưu ý:
# - Không lưu bài tập vào Database.
# - Không chấm điểm tại Backend.
# - Không tạo thêm loại câu hỏi mới ngoài contract.


# 6. KIỂM TRA
#
# TODO:
# - Model trả JSON hợp lệ.
# - Model trả JSON không parse được.
# - Model trả thiếu câu hỏi.
# - Model trả nhiều câu hơn yêu cầu.
# - Model tạo đáp án không tồn tại.
# - Model tạo question_id trùng nhau.
# - Model tạo 2 đáp án đúng cho loại một đáp án.
# - Model tạo dưới 2 đáp án đúng cho loại nhiều đáp án.
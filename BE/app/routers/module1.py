# ============================================================
# FILE: app/routers/module1.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Cung cấp API sinh bài tập trắc nghiệm.
#
# Module 1 chỉ sinh câu hỏi.
# Frontend tự chấm điểm dựa trên correct_option_ids.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - app.database.get_supabase
# - app.schemas.module1:
#     QuizGenerateRequest, QuizGenerateResponse
# - app.egm.module1_egm.generate_quiz
#
# Khởi tạo router với prefix="/api/exercises/quiz".


# 2. HÀM generate_quiz()
#
# Endpoint:
# POST /api/exercises/quiz/generate
#
# Input:
# - QuizGenerateRequest
#
# Output:
# - QuizGenerateResponse
#
# TODO:
# Bước 1:
#     Nhận cấu hình bài tập từ FE.
#
# Bước 2:
#     Kiểm tra request bằng Pydantic.
#
# Bước 3:
#     Truy vấn child_profiles theo child_id.
#
# Bước 4:
#     Nếu hồ sơ không tồn tại, trả HTTP 404.
#
# Bước 5:
#     Lấy age và các sở thích cần thiết của trẻ.
#
# Bước 6:
#     Gọi generate_quiz() trong module1_egm.py.
#     Truyền vào cấu hình bài và thông tin phù hợp của trẻ.
#
# Bước 7:
#     Nhận dữ liệu bài tập đã được EGM kiểm tra.
#
# Bước 8:
#     Đóng gói thành QuizGenerateResponse.
#
# Bước 9:
#     Trả HTTP 200 cho FE.


# 3. XỬ LÝ LỖI
#
# TODO:
# - child_id không tồn tại -> 404.
# - question_count không hợp lệ -> 422.
# - Request không hợp lệ -> 422.
# - Model output sai schema -> 502.
# - LLM Server không khả dụng -> 503.
# - LLM Server timeout -> 504.


# 4. QUY ƯỚC
#
# - Không viết prompt trực tiếp trong Router.
# - Không gửi HTTP request trực tiếp đến LLM Server.
# - Không tự parse JSON do LLM sinh trong Router.
# - Không chấm điểm trắc nghiệm.
# - Không lưu câu hỏi vào Database.
#
# Lưu ý về ownership:
# Request thiết kế hiện tại chỉ chứa child_id, không có user_id.
# Vì vậy không thể kiểm tra hồ sơ thuộc user_id nào
# nếu không bổ sung thông tin vào contract.
# Với bản demo hiện tại, chỉ kiểm tra child_id tồn tại.


# 5. KIỂM TRA API
#
# TODO:
# - Sinh bài trắc nghiệm một đáp án.
# - Sinh bài trắc nghiệm nhiều đáp án.
# - Sinh bài với 1 câu.
# - Sinh bài với 5 câu.
# - Gửi child_id không tồn tại.
# - Mô phỏng LLM trả dữ liệu lỗi.
# ============================================================
# FILE: app/routers/module2.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Cung cấp hai API:
# - Sinh câu hỏi mở.
# - Đánh giá câu trả lời của trẻ.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - app.database.get_supabase
# - app.schemas.module2:
#     OpenGenerateRequest, OpenGenerateResponse,
#     OpenEvaluateRequest, OpenEvaluateResponse
# - app.egm.module2_egm:
#     generate_open_questions, evaluate_open_answer
#
# Khởi tạo router với prefix="/api/exercises/open".


# 2. HÀM generate_open_questions()
#
# Endpoint:
# POST /api/exercises/open/generate
#
# Input:
# - OpenGenerateRequest
#
# Output:
# - OpenGenerateResponse
#
# TODO:
# Bước 1:
#     Nhận cấu hình bài tập.
#
# Bước 2:
#     Kiểm tra request.
#
# Bước 3:
#     Truy vấn hồ sơ trẻ theo child_id.
#
# Bước 4:
#     Lấy độ tuổi của trẻ.
#
# Bước 5:
#     Gọi EGM sinh câu hỏi mở.
#
# Bước 6:
#     Nhận danh sách câu hỏi đã được kiểm tra.
#
# Bước 7:
#     Trả response cho FE.


# 3. HÀM evaluate_open_answer()
#
# Endpoint:
# POST /api/exercises/open/evaluate
#
# Input:
# - OpenEvaluateRequest
#
# Output:
# - OpenEvaluateResponse
#
# TODO:
# Bước 1:
#     Nhận câu hỏi, câu trả lời và tiêu chí đánh giá.
#
# Bước 2:
#     Kiểm tra dữ liệu đầu vào.
#
# Bước 3:
#     Nếu câu trả lời rỗng, trả HTTP 422.
#
# Bước 4:
#     Kiểm tra child_id tồn tại và lấy độ tuổi.
#
# Bước 5:
#     Gọi evaluate_open_answer() trong EGM.
#
# Bước 6:
#     Nhận kết quả đánh giá đã chuẩn hóa.
#
# Bước 7:
#     Trả điểm và nhận xét cho FE.


# 4. XỬ LÝ LỖI
#
# TODO:
# - Hồ sơ trẻ không tồn tại.
# - Câu trả lời rỗng.
# - LLM Server không phản hồi.
# - Model trả dữ liệu không đúng cấu trúc.
# - Model trả điểm nằm ngoài thang 0 đến 10.
#
# Trả thông báo phù hợp, bằng tiếng Việt.


# 5. QUY ƯỚC
#
# - Không trực tiếp viết prompt trong Router.
# - Không xử lý kết quả model bằng cách đoán cấu trúc.
# - Không lưu lịch sử bài làm vào Database.
# - Đánh giá từng câu, không bắt buộc chấm toàn bộ bài.
# - Điểm LLM là đánh giá tham khảo.
#
# Tương tự Module 1, request hiện tại chỉ chứa child_id;
# việc kiểm tra sở hữu hồ sơ yêu cầu thống nhất thêm contract.


# 6. KIỂM TRA API
#
# TODO:
# - Sinh câu hỏi mở thành công.
# - Sinh đủ số lượng câu hỏi yêu cầu.
# - Đánh giá câu trả lời hợp lệ.
# - Đánh giá câu trả lời diễn đạt khác đáp án mẫu.
# - Đánh giá câu trả lời trống.
# - Mô phỏng lỗi LLM.
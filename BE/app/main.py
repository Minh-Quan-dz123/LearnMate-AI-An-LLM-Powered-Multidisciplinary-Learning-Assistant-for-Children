# ============================================================
# FILE: app/main.py
# PHỤ TRÁCH: ________
#
# MỤC ĐÍCH:
# Khởi tạo ứng dụng FastAPI và đăng ký toàn bộ API Router.
# Đây là điểm bắt đầu của Backend.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.FastAPI:
#     Khởi tạo ứng dụng FastAPI.
#
# - fastapi.middleware.cors.CORSMiddleware: (optional)
#     Cho phép Frontend gọi API từ một origin khác.
#
# - app.routers.auth
# - app.routers.children
# - app.routers.module1
# - app.routers.module2
#     Các router nghiệp vụ của Backend.
#
# - app.config.get_settings:
#     Lấy cấu hình ứng dụng nếu cần.


# 2. KHỞI TẠO FASTAPI
#
# TODO:
# - Tạo biến app = FastAPI(...).
# - Đặt title: "LearnMate AI Backend".
# - Đặt version cho ứng dụng.
# - Có thể cấu hình thông tin Swagger API.


# 3. CẤU HÌNH CORS
#
# TODO:
# - Thêm CORSMiddleware.
# - Cho phép origin của Frontend đang chạy local.
# - Cho phép các HTTP method cần thiết.
# - Cho phép Content-Type và các header cần thiết.
# - Không cần cấu hình cookie xác thực trong MVP.


# 4. ĐĂNG KÝ ROUTER
#
# TODO:
# - Đăng ký auth.router.
# - Đăng ký children.router.
# - Đăng ký module1.router.
# - Đăng ký module2.router.
#
# Lưu ý:
# Mỗi router tự khai báo prefix của mình.
# Không khai báo trùng prefix khi include_router.


# 5. HÀM health_check()
#
# Endpoint:
# GET /health
#
# Input:
# - Không có.
#
# Output:
# - JSON thông báo Backend đang hoạt động.
#
# TODO:
# - Khai báo endpoint.
# - Trả về trạng thái hoạt động của ứng dụng.
# - Không cần kiểm tra LLM hoặc Database trong health check
#   đơn giản của bản thử nghiệm.


# 6. XỬ LÝ LỖI CHUNG (TÙY CHỌN)
#
# TODO:
# - Có thể viết exception handler dùng chung.
# - Chuyển lỗi nội bộ thành thông báo tiếng Việt.
# - Chuẩn hóa response lỗi.
# - Không trả thông tin bí mật hoặc stack trace về FE.
#
# Response lỗi đề xuất:
# {
#   "success": false,
#   "message": "Thông báo lỗi tiếng Việt",
#   "error": {"code": "ERROR_CODE"}
# }


# 7. KHỞI ĐỘNG
#
# Chạy tại thư mục gốc:
# python -m uvicorn app.main:app --reload
#
# Swagger:
# http://127.0.0.1:8000/docs
#
# Health:
# http://127.0.0.1:8000/health
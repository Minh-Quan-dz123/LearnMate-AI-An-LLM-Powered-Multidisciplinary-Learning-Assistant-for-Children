# ============================================================
# FILE: app/main.py
# PHỤ TRÁCH: Quân
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


# 1. IMPORT THƯ VIỆN
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_supabase_client
from app.routers import auth, children, module1, module2

# 2. QUẢN LÝ VÒNG ĐỜI ỨNG DỤNG
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Bước 1: Khởi tạo Supabase Async Client.
    # Thực hiện một lần khi ứng dụng khởi động.
    supabase = await create_supabase_client()

    # Bước 2: Lưu client vào application state.
    # Các Router có thể truy cập thông qua Depends().
    app.state.supabase = supabase

    try:
        # Ứng dụng bắt đầu phục vụ HTTP request.
        yield

    finally:
        # Bước 3: Giải phóng kết nối PostgREST
        # khi ứng dụng dừng.
        await supabase.postgrest.aclose()

# 3. KHỞI TẠO FASTAPI
app = FastAPI(
    title="LearnMate AI Backend",
    description="Backend API cho hệ thống LearnMate AI",
    version="1.0.0",
    lifespan=lifespan
)

# 4. CẤU HÌNH CORS
# Các địa chỉ Frontend được phép gọi Backend.
# Sử dụng trong môi trường local/demo.

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=False,

    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],

    allow_headers=["Content-Type"],

)

# 5. ĐĂNG KÝ ROUTER
# Module quản lý tài khoản.
# Đăng ký API quản lý tài khoản.
app.include_router(auth.router)

# Đăng ký API quản lý hồ sơ trẻ.
app.include_router(children.router)

# Đăng ký API sinh trắc nghiệm Module 1.
app.include_router(module1.router)

# Đăng ký API sinh trắc nghiệm Module 2.
app.include_router(module2.router)

# Các Router sau sẽ đăng ký khi đã triển khai:
#
# from app.routers import children, module1, module2
#
# app.include_router(children.router)
# app.include_router(module1.router)
# app.include_router(module2.router)


# 6. API KIỂM TRA TRẠNG THÁI
@app.get("/health")
async def health_check():

    return {
        "success": True,
        "message": "Backend đang hoạt động"
    }

# 7. KHỞI ĐỘNG
# Chạy tại thư mục gốc:
#
# python -m uvicorn app.main:app --reload
#
# Swagger:
# http://127.0.0.1:8000/docs
#
# Health:
# http://127.0.0.1:8000/health

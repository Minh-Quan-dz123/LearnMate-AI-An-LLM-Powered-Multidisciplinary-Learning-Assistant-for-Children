
"""
FILE: app/main.py

MỤC ĐÍCH:
    1. Khởi tạo ứng dụng FastAPI.
    2. Đăng ký các API Router.
    3. Tạo API /health để kiểm tra trạng thái server.
    4. Cung cấp giao diện Swagger tự động.

KIẾN TRÚC:
    Backend (BE)
        |
        | HTTP POST
        v
    LLM_V1/app/main.py
        |
        v
    app/routers/llm.py
        |
        v
    app/providers/gemini.py
        |
        v
    Gemini API

CÁCH CHẠY:
    Từ thư mục LLM_V1:

    python -m uvicorn app.main:app --reload --port 8001

TRUY CẬP:
    http://127.0.0.1:8001/docs
    http://127.0.0.1:8001/health
"""


# ==================================================
# 1. IMPORT THƯ VIỆN
# ==================================================

# FastAPI:
#     Class do thư viện fastapi cung cấp.
#
# Dùng để khởi tạo ứng dụng HTTP API,
# quản lý request, response và các endpoint.
from fastapi import FastAPI


# Import router đã xây dựng tại:
# app/routers/llm.py
#
# Trong llm.py có:
#     router = APIRouter(...)
#
# "as llm_router":
#     Đặt bí danh cho đối tượng router được import.
#
# Ví dụ:
#     llm_router thay cho tên router thông thường.
from app.routers.llm import router as llm_router


# ==================================================
# 2. KHỞI TẠO ỨNG DỤNG FASTAPI
# ==================================================

# FastAPI(...) tạo một instance của class FastAPI.
#
# Instance là một đối tượng được tạo từ class.
#
# title:
#     Tên ứng dụng xuất hiện trong Swagger.
#
# description:
#     Mô tả chức năng của API Server.
#
# version:
#     Phiên bản ứng dụng do chúng ta quy định.
#
# docs_url:
#     Đường dẫn hiển thị giao diện Swagger UI.
#
# redoc_url:
#     Đường dẫn hiển thị tài liệu ReDoc.
#
# Ví dụ:
#     GET http://127.0.0.1:8001/docs
#
#     -> Hiển thị Swagger UI.
app = FastAPI(
    title="LearnMate AI - LLM_V1 Server",

    description=(
        "LLM Server độc lập sử dụng Gemini API "
        "để sinh và đánh giá nội dung học tập."
    ),

    version="1.0.0",

    docs_url="/docs",

    redoc_url="/redoc"
)


# ==================================================
# 3. ĐĂNG KÝ ROUTER VÀO ỨNG DỤNG
# ==================================================

# include_router():
#     Phương thức của đối tượng FastAPI.
#
# Chức năng:
#     Đăng ký các endpoint được định nghĩa
#     trong một APIRouter vào ứng dụng chính.
#
# llm_router:
#     Router được import từ app/routers/llm.py.
#
# Router này đang chứa:
#     POST /internal/llm/generate
#
# Nếu không gọi include_router():
#     Endpoint trong llm.py sẽ không được
#     đăng ký vào ứng dụng FastAPI này.
app.include_router(llm_router)


# ==================================================
# 4. API KIỂM TRA SỨC KHỎE SERVER
# ==================================================

# @app.get("/health"):
#     Decorator đăng ký endpoint GET /health.
#
# Khi client gửi:
#     GET http://127.0.0.1:8001/health
#
# FastAPI thực thi hàm health_check().
#
# tags:
#     Tên nhóm endpoint trong Swagger.
#
# summary:
#     Nội dung mô tả ngắn trong Swagger.
@app.get(
    "/health",
    tags=["Health"],
    summary="Kiểm tra trạng thái LLM Server"
)
async def health_check() -> dict:
    """
    Kiểm tra xem ứng dụng FastAPI có hoạt động không.

    THAM SỐ:
        Không có.

    KIỂU TRẢ VỀ:
        dict:
            Dictionary của Python.

    VÍ DỤ:
        {
            "success": True,
            "message": "LLM_V1 Server đang hoạt động",
            "version": "1.0.0"
        }

    LƯU Ý:
        API này không gọi Gemini.

        Nó chỉ xác nhận FastAPI Server đang chạy.
        Không xác nhận API key hay Gemini đang online.
    """

    # return trả về dictionary cho FastAPI.
    #
    # FastAPI tự chuyển Python dict thành JSON.
    #
    # Python True sẽ thành JSON true.
    return {
        "success": True,
        "message": "LLM_V1 Server đang hoạt động",
        "version": "1.0.0"
    }

# ============================================================
# FILE: app/routers/auth.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Cung cấp API đăng ký và đăng nhập tài khoản.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - app.database.get_supabase
# - app.schemas.auth:
#     RegisterRequest, LoginRequest, AuthData, AuthResponse
#
# Khởi tạo router với prefix="/api/auth".


# 2. HÀM register()
#
# Endpoint:
# POST /api/auth/register
#
# Input:
# - RegisterRequest
#
# Output:
# - AuthResponse
#
# TODO:
# Bước 1:
#     Nhận request đăng ký.
#
# Bước 2:
#     Kiểm tra dữ liệu bằng Pydantic.
#
# Bước 3:
#     Sử dụng get_supabase() lấy client.
#
# Bước 4:
#     Kiểm tra username đã tồn tại trong users hay chưa.
#
# Bước 5:
#     Nếu đã tồn tại, trả HTTP 409.
#
# Bước 6:
#     Thêm tài khoản mới vào bảng users.
#
# Bước 7:
#     Lấy id và username của tài khoản vừa tạo.
#
# Bước 8:
#     Trả HTTP 201 cùng AuthResponse.
#
# Lưu ý:
# - Không trả password.
# - Không tạo JWT hoặc session.
# - Chỉ dùng tài khoản và mật khẩu giả cho demo.
# - Cần bắt cả lỗi UNIQUE từ Database để tránh tạo trùng.


# 3. HÀM login()
#
# Endpoint:
# POST /api/auth/login
#
# Input:
# - LoginRequest
#
# Output:
# - AuthResponse
#
# TODO:
# Bước 1:
#     Nhận username và password.
#
# Bước 2:
#     Truy vấn users theo username.
#
# Bước 3:
#     Nếu tài khoản không tồn tại, trả HTTP 401.
#
# Bước 4:
#     Kiểm tra password theo cách lưu mật khẩu đã chọn
#     cho bản demo.
#
# Bước 5:
#     Nếu thông tin không đúng, trả HTTP 401.
#
# Bước 6:
#     Trả về user_id và username.
#
# Bước 7:
#     Frontend tự lưu user_id để sử dụng tiếp.
#
# Lưu ý:
# - Không trả token.
# - Đăng xuất được thực hiện bằng cách FE xóa user_id.


# 4. XỬ LÝ LỖI
#
# TODO:
# - Username bị trùng.
# - Username/password không hợp lệ.
# - Truy vấn Supabase thất bại.
# - Đảm bảo thông báo trả về bằng tiếng Việt.


# 5. KIỂM TRA API
#
# TODO:
# - Đăng ký tài khoản mới.
# - Đăng ký tài khoản trùng.
# - Đăng nhập đúng.
# - Đăng nhập sai mật khẩu.
# - Đăng nhập tài khoản không tồn tại.

# 1. IMPORT THƯ VIỆN
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from supabase import AsyncClient
from postgrest.exceptions import APIError

from app.database import get_supabase

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthData,
    AuthResponse,
)

# 2. KHỞI TẠO ROUTER
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# 3. HÀM TRẢ RESPONSE LỖI
def error_response(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": {
                "code": code, 
                "details": None
            }
        }
    )

# 4. ĐĂNG KÝ TÀI KHOẢN
# POST /api/auth/register

# Decorator đăng ký hàm register() để xử lý HTTP POST request.
# response_model=AuthResponse giúp FastAPI kiểm tra và tuần tự hóa response thành công theo Pydantic schema, đồng thời tạo tài liệu API.
@router.post("/register", response_model=AuthResponse, status_code = 201)
async def register(request: RegisterRequest, db: AsyncClient = Depends(get_supabase)):

    """
    Đăng ký tài khoản mới.

    Input:
        request: RegisterRequest.
        db: Supabase AsyncClient.

    Output:
        AuthResponse.

    Quy trình:
        1. Nhận và kiểm tra request.
        2. Kiểm tra username đã tồn tại.
        3. Thêm tài khoản vào Database.
        4. Trả user_id và username.
    """

    try:
        #B1: kiểm tra usename đã tồn tại chưa
        existing = await (
            db.table("users")
            .select("id")
            .eq("username", request.username)
            .limit(1)
            .execute()
        )

        if existing.data:
            return error_response(409, "Tên đăng nhập đã tồn tại", "USERNAME_ALREADY_EXISTS")

        #B2: nếu chưa thì cho phép thêm tài khoản vào database
        result = await (
            db.table("users")
            .insert({
                "username": request.username,
                "password": request.password
            })
            .select("id, username")
            .execute()
        )
        
        # BƯỚC 3: KIỂM TRA KẾT QUẢ INSERT
        if not result.data:
            return error_response(
                status_code=503,
                message="Không thể tạo tài khoản",
                code="DATABASE_ERROR"
            )

        # BƯỚC 4: LẤY THÔNG TIN TÀI KHOẢN và TRẢ RESPONSE THÀNH CÔNG
        user = result.data[0]

        return AuthResponse(
            success=True,
            message="Tạo tài khoản thành công",

            data=AuthData(
                user_id=user["id"],
                username=user["username"]
            )
        )

    # XỬ LÝ LỖI SUPABASE / POSTGRESQL
    except APIError as exc:
        # Database báo vi phạm UNIQUE
        if exc.code == "23505":
            return error_response(
                409,
                "Tên đăng nhập đã tồn tại",
                "USERNAME_ALREADY_EXISTS"
            )

        return error_response(
            503,
            "Không thể truy cập cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    # XỬ LÝ LỖI KHÔNG MONG ĐỢI
    except Exception:
        return error_response(
            503,
            "Không thể kết nối cơ sở dữ liệu",
            "DATABASE_UNAVAILABLE"
        )

# 5. ĐĂNG NHẬP TÀI KHOẢN
# POST /api/auth/login
@router.post("/login", response_model=AuthResponse, status_code=200)
async def login(request: LoginRequest,  db: AsyncClient = Depends(get_supabase)):

    """
    Đăng nhập tài khoản.

    Input:
        request: LoginRequest.
        db: Supabase AsyncClient.

    Output:
        AuthResponse.

    Quy trình:
        1. Nhận username và password.
        2. Tìm tài khoản trong Database.
        3. Kiểm tra mật khẩu demo.
        4. Trả user_id và username.
    """

    try:
        # BƯỚC 1: TRUY VẤN USERNAME
        result = await (
            db.table("users")
            .select("id, username, password")
            .eq("username", request.username)
            .limit(1)
            .execute()
        )

        # BƯỚC 2: KIỂM TRA TÀI KHOẢN TỒN TẠI
        if not result.data:

            return error_response(
                status_code=401,
                message="Tên đăng nhập hoặc mật khẩu không đúng",
                code="INVALID_CREDENTIALS"
            )

        # BƯỚC 3: LẤY THÔNG TIN TÀI KHOẢN
        user = result.data[0]

        # BƯỚC 4: KIỂM TRA MẬT KHẨU
 
        # Cách so sánh này chỉ dành cho tài khoản demo,
        # dùng dữ liệu giả theo thiết kế prototype.
        #
        # Khi triển khai thực tế phải dùng password hash.

        if user["password"] != request.password:

            return error_response(
                status_code=401,
                message="Tên đăng nhập hoặc mật khẩu không đúng",
                code="INVALID_CREDENTIALS"
            )

        # BƯỚC 5: TRẢ RESPONSE THÀNH CÔNG
        return AuthResponse(
            success=True,
            message="Đăng nhập thành công",

            data=AuthData(
                user_id=user["id"],
                username=user["username"]
            )
        )

    # --------------------------------------------------------
    # XỬ LÝ LỖI DATABASE
    # --------------------------------------------------------

    except APIError:

        return error_response(
            status_code=503,
            message="Không thể truy cập cơ sở dữ liệu",
            code="DATABASE_ERROR"
        )

    # --------------------------------------------------------
    # XỬ LÝ LỖI KHÔNG MONG ĐỢI
    # --------------------------------------------------------

    except Exception:

        return error_response(
            status_code=503,
            message="Không thể kết nối cơ sở dữ liệu",
            code="DATABASE_UNAVAILABLE"
        )
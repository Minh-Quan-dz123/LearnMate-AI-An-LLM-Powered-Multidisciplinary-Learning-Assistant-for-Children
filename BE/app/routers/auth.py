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
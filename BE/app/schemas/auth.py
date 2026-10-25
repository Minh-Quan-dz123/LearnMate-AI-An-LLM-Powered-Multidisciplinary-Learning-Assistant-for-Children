# ============================================================
# FILE: app/schemas/auth.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Định nghĩa Request và Response cho:
# - Đăng ký tài khoản.
# - Đăng nhập tài khoản.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel:
#     Định nghĩa model dữ liệu.
#
# - pydantic.Field:
#     Khai báo ràng buộc cho các trường.
#
# - pydantic.field_validator / model_validator:
#     Tùy chọn nếu cần kiểm tra dữ liệu liên quan nhau.


# 2. CLASS RegisterRequest
#
# Các trường:
# - username: str
# - password: str
# - confirm_password: str
#
# TODO:
# - Kiểm tra username không rỗng.
# - Kiểm tra password không rỗng.
# - Kiểm tra confirm_password trùng password.
# - Giới hạn độ dài dữ liệu phù hợp Database.
#
# Lưu ý:
# confirm_password có thể được kiểm tra hoàn toàn trên FE
# nếu hai bên thống nhất không truyền trường này.


# 3. CLASS LoginRequest
#
# Các trường:
# - username: str
# - password: str
#
# TODO:
# - Kiểm tra các trường bắt buộc.
# - Không thực hiện truy vấn Database ở đây.


# 4. CLASS AuthData
#
# Dữ liệu trả về khi đăng ký/đăng nhập thành công:
#
# - user_id: int
# - username: str
#
# Không trả password về Frontend.


# 5. CLASS AuthResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: AuthData
#
# Ví dụ:
# {
#   "success": true,
#   "message": "Đăng nhập thành công",
#   "data": {
#     "user_id": 1,
#     "username": "be_an_01"
#   }
# }


# 6. KIỂM TRA
#
# TODO:
# - Thử tạo RegisterRequest hợp lệ.
# - Thử username rỗng.
# - Thử password rỗng.
# - Thử confirm_password không trùng.
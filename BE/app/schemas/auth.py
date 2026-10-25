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
# 1. IMPORT THƯ VIỆN
from pydantic import BaseModel, Field, field_validator, model_validator

# BaseModel là class nền tảng của Pydantic, được sử dụng để định 
# nghĩa cấu trúc dữ liệu và kiểm tra dữ liệu đầu vào.


# 1 LOGIN REQUEST
class LoginRequest(BaseModel):
    """
    Dữ liệu Frontend gửi khi đăng nhập.

    Fields:
        username: Tên đăng nhập.
        password: Mật khẩu.
    """

    # Field() được dùng để khai báo thêm ràng buộc cho trường dữ liệu.
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length = 120)

    # VALIDATE USERNAME
    # @field_validator là decorator để bổ sung logic kiểm tra cho một trường cụ thể.
    # Ở đây:
    # 1. Pydantic nhận giá trị username.
    # 2. Hàm validate_username() được gọi.
    # 3. .strip() loại bỏ khoảng trắng ở đầu và cuối.
    # 4. Nếu sau khi loại bỏ khoảng trắng mà chuỗi rỗng, phát sinh ValueError.
    # 5. Nếu hợp lệ, trả giá trị đã xử lý.
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Tên đăng nhập ko được để trống")

        # Trả giá trị sau khi xử lý.
        return value
    # @classmethod cho phép nhận class qua tham số cls, dù hàm hiện chưa cần sử dụng đến nó.

    # VALIDATE PASSWORD
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Mật khẩu không được để trống")

        return value

# 3. REGISTER REQUEST
class RegisterRequest(LoginRequest): # RegisterRequest kế thừa LoginRequest để tận dụng code

    """
    Dữ liệu Frontend gửi khi đăng ký.

    Kế thừa LoginRequest:
        - username
        - password

    Bổ sung:
        - confirm_password
    """
        
    confirm_password: str = Field(min_length=1, max_length=120)

    # mode="after" có nghĩa là hàm chạy sau khi các trường đã được 
    # Pydantic xử lý và kiểm tra cơ bản thành công
    @model_validator(mode = "after")
    def validate_confirm_password(self):
        if self.password != self.confirm_password:
            raise ValueError("Mật khẩu không khớp")
        return self

# 4. AUTH DATA
class AuthData(BaseModel):
    """
    Thông tin tài khoản trả về Frontend.

    Fields:
        user_id: ID người dùng trong Database.
        username: Tên đăng nhập.

    Không trả password.
    """

    user_id: int
    username: str

# 5. AUTH RESPONSE
class AuthResponse(BaseModel):
    success: bool
    message: str
    data: AuthData

    """
    Cấu trúc response khi đăng ký/đăng nhập thành công.

    Example:
    {
        "success": true,
        "message": "Đăng nhập thành công",
        "data": {
            "user_id": 1,
            "username": "demo"
        }
    }
    """



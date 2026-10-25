# ============================================================
# FILE: app/config.py
# PHỤ TRÁCH: _______
#
# MỤC ĐÍCH:
# Đọc và quản lý các biến cấu hình của Backend.
# Không viết cứng URL, API Key vào mã nguồn.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic_settings.BaseSettings:
#     Đọc biến môi trường và kiểm tra kiểu dữ liệu.
#
# - pydantic_settings.SettingsConfigDict:
#     Cấu hình cách đọc file .env.
#
# - functools.lru_cache: (optional)
#     Tùy chọn, tránh khởi tạo Settings nhiều lần.


# 2. CLASS Settings
#
# TODO:
# - Tạo class Settings kế thừa BaseSettings.
# - Khai báo các trường cấu hình sau:
#
# SUPABASE_URL: str
#     URL project Supabase.
#
# SUPABASE_KEY: str
#     API key sử dụng ở Backend.
#     Không gửi giá trị này về Frontend.
#
# LLM_SERVER_URL: str
#     Địa chỉ của LLM Server.
#
# LLM_TIMEOUT_SECONDS: float
#     Thời gian chờ tối đa khi gọi LLM Server.
#
# LLM_GENERATION_MODEL: str
#     Tên hoặc nhãn logic của model sinh câu hỏi.
#     Tùy chọn, cần thống nhất với LLM Server.
#
# LLM_EVALUATION_MODEL: str
#     Tên hoặc nhãn logic của model đánh giá.
#     Tùy chọn, có thể dùng chung model sinh câu hỏi.
#
# LLM_INTERNAL_API_KEY: str | None
#     Tùy chọn nếu LLM Server sử dụng shared secret.
#
# TODO:
# - Cấu hình đọc biến từ file .env.
# - Kiểm tra các giá trị cấu hình cần thiết.
# - Đặt giá trị mặc định cho cấu hình không bắt buộc.


# 3. HÀM get_settings()
#
# Input:
# - Không có.
#
# Output:
# - Một instance của Settings.
#
# TODO:
# - Khởi tạo Settings.
# - Trả về object cấu hình.
# - Có thể dùng lru_cache để tái sử dụng.
#
# Lưu ý:
# - Không commit file .env lên Git.
# - Không in API Key ra terminal khi debug.
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Class chứa cấu hình của BE
class Settings(BaseSettings):
    # cấu hình Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # cấu hình LLM Server
    LLM_SERVER_URL: str = "http://127.0.0.1:8001"
    LLM_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        gt=0
    )

    # cấu hình model
    LLM_GENERATION_MODEL: str = "default"
    LLM_EVALUATION_MODEL: str = "default"

    # Khóa nội bộ để dùng nếu LLM Server yêu cầu
    LLM_INTERNAL_API_KEY: str | None = None

    # Khai báo là đọc dữ liệu từ file .env
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# hàm lấy cấu hình

# Decorator trong Python là một cơ chế cho 
# phép bổ sung hoặc thay đổi hành vi của một 
# hàm mà không cần sửa code bên trong hàm đó

# @lru_cache là một decorator trong Python, dùng 
# để lưu kết quả trả về của hàm vào bộ nhớ 
# (cache), giúp những lần gọi sau với cùng tham số 
# không cần thực thi lại hàm.

@lru_cache
def get_settings() -> Settings: 
    return Settings()
# trả về object có thể đọc cấu hình
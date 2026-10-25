# ============================================================
# FILE: app/database.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Khởi tạo Supabase Client để Backend thao tác Database.
#
# Database sử dụng:
# - users
# - child_profiles
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - supabase.create_client:
#     Khởi tạo client kết nối Supabase.
#
# - supabase.Client:
#     Type hint cho Supabase Client.
#
# - app.config.get_settings:
#     Đọc URL và API Key.
#
# - functools.lru_cache:
#     Tùy chọn, tái sử dụng client.


# 2. HÀM get_supabase()
#
# Input:
# - Không có.
#
# Output:
# - Supabase Client.
#
# TODO:
# Bước 1:
#     Lấy SUPABASE_URL và SUPABASE_KEY từ Settings.
#
# Bước 2:
#     Gọi create_client() để khởi tạo kết nối.
#
# Bước 3:
#     Trả về Supabase Client.
#
# Bước 4:
#     Có thể cache client để tái sử dụng.
#
# Lưu ý:
# - Các Router sử dụng client này để truy vấn.
# - Không tự khởi tạo client riêng trong từng Router.
# - Nếu dùng Supabase SDK đồng bộ bên trong async endpoint,
#   cần tránh chặn event loop; có thể chọn client async.


# 3. CẤU TRÚC DATABASE DỰ KIẾN
#
# TABLE users:
# - id: BIGINT, Primary Key
# - username: VARCHAR, UNIQUE
# - password: TEXT
#
# TABLE child_profiles:
# - id: BIGINT, Primary Key
# - user_id: BIGINT, Foreign Key -> users.id
# - name: VARCHAR
# - age: INTEGER
# - gender: VARCHAR, nullable
# - interests: danh sách sở thích
#
# Quan hệ:
# Một User có thể có nhiều Child Profile.


# 4. QUY ƯỚC THAO TÁC
#
# TODO:
# - Truy vấn đúng bảng và tên cột đã tạo trên Supabase.
# - Kiểm tra response của thao tác Database.
# - Xử lý trường hợp không tìm thấy bản ghi.
# - Không trực tiếp trả lỗi Database thô về Frontend.
#
# Lưu ý:
# - Chỉ dùng tài khoản và dữ liệu giả cho prototype.
# - Không triển khai hệ thống xác thực production tại đây.

# 1. IMPORT THƯ VIỆN
from fastapi import Request
from supabase import acreate_client, AsyncClient
from app.config import get_settings

# 2. KHỞI TẠO SUPABASE CLIENT
async def create_supabase_client() -> AsyncClient:

    """
    Khởi tạo Supabase Async Client.
    Input: Không có.
    Output: AsyncClient.

    Chức năng:
        - Đọc cấu hình từ config.py.
        - Khởi tạo client bất đồng bộ.
        - Trả client cho FastAPI lifespan.
    """

    # Bước 1: Lấy cấu hình.
    settings = get_settings()

    # Bước 2: Khởi tạo Supabase Async Client.
    client: AsyncClient = await acreate_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )

    # Bước 3: Trả client.
    return client

# 3. DEPENDENCY CUNG CẤP DATABASE CLIENT
# Lấy Supabase Client đã được khởi tạo để cung cấp cho các 
# Router thông qua Dependency Injection (DI).
async def get_supabase(request: Request) -> AsyncClient:

    """
    Cung cấp Supabase Client cho Router.
    Input:
        request: Request
            HTTP request hiện tại.

    Output:
        AsyncClient.

    Chức năng:
        - Lấy client đã lưu trong app.state.
        - Không tạo lại client cho mỗi request.
    """

    return request.app.state.supabase


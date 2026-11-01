
"""
MODULE QUẢN LÝ CẤU HÌNH LLM_V1

Mục đích:
    1. Đọc thông tin cấu hình từ file .env.
    2. Kiểm tra cấu hình bắt buộc.
    3. Chuyển đổi dữ liệu về kiểu phù hợp.
    4. Cung cấp cấu hình cho các module khác.

Ví dụ sử dụng:
    from app.config import get_settings

    settings = get_settings()
    print(settings.gemini_model)
"""

# ==================================================
# 1. IMPORT THƯ VIỆN
# ==================================================

# os là thư viện chuẩn Python.
# getenv() dùng để đọc biến môi trường.
import os

# Path giúp làm việc với đường dẫn file/thư mục.
from pathlib import Path

# dataclass tự động tạo các phương thức cho class,
# ví dụ __init__(), __repr__(), __eq__().
from dataclasses import dataclass

# load_dotenv() đọc các biến KEY=VALUE từ file .env.
from dotenv import load_dotenv


# ==================================================
# 2. XÁC ĐỊNH ĐƯỜNG DẪN FILE .env
# ==================================================

# __file__ là đường dẫn file config.py đang chạy.
#
# Ví dụ:
# D:/project_LLM/LLM_V1/app/config.py
#
# resolve() -> lấy đường dẫn tuyệt đối.
# parents[0] -> thư mục app/
# parents[1] -> thư mục LLM_V1/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Toán tử / của pathlib.Path nối đường dẫn.
#
# Ví dụ:
# PROJECT_ROOT = D:/project_LLM/LLM_V1
# ENV_PATH = D:/project_LLM/LLM_V1/.env
ENV_PATH = PROJECT_ROOT / ".env"

# Đọc .env và nạp các biến vào môi trường Python.
#
# dotenv_path: chỉ định file .env cần đọc.
#
# Mặc định, biến môi trường đã tồn tại sẽ được
# ưu tiên hơn giá trị trong file .env.
load_dotenv(dotenv_path=ENV_PATH)


# ==================================================
# 3. CLASS LƯU TRỮ CẤU HÌNH
# ==================================================

@dataclass(frozen=True)
class Settings:
    """
    Đối tượng chứa cấu hình của LLM_V1.

    @dataclass:
        Decorator tự tạo __init__ và các phương
        thức tiện ích dựa trên những thuộc tính
        khai báo trong class.

    frozen=True:
        Ngăn gán lại thuộc tính sau khi khởi tạo.

    Ví dụ:
        settings = Settings(
            gemini_api_key="abc",
            gemini_model="gemini-3.5-flash-lite",
            llm_provider="gemini",
            llm_host="127.0.0.1",
            llm_port=8001
        )

        settings.llm_port -> 8001
    """

    # str: kiểu chuỗi ký tự.
    gemini_api_key: str

    # Model Gemini được sử dụng.
    gemini_model: str

    # Nhà cung cấp LLM hiện tại.
    llm_provider: str

    # Địa chỉ IP mà FastAPI lắng nghe.
    llm_host: str

    # int: kiểu số nguyên, ví dụ 8001.
    llm_port: int


# ==================================================
# 4. HÀM ĐỌC VÀ KIỂM TRA CẤU HÌNH
# ==================================================

def get_settings() -> Settings:
    """
    Đọc biến môi trường và trả về Settings.

    Đầu vào:
        Không có tham số.

    Đầu ra:
        Đối tượng Settings.

    Nếu thiếu API key hoặc port không hợp lệ,
    chương trình sẽ phát sinh ValueError.
    """

    # os.getenv("KEY", "DEFAULT"):
    # - Đọc biến môi trường có tên KEY.
    # - Nếu không tồn tại, dùng giá trị DEFAULT.
    #
    # strip() loại bỏ khoảng trắng ở đầu và cuối.
    api_key = os.getenv(
        "GEMINI_API_KEY", ""
    ).strip()

    model = os.getenv(
        "GEMINI_MODEL", "gemini-3.5-flash-lite"
    ).strip()

    provider = os.getenv(
        "LLM_PROVIDER", "gemini"
    ).strip().lower()

    host = os.getenv(
        "LLM_HOST", "127.0.0.1"
    ).strip()

    # Biến môi trường luôn được đọc dưới dạng str.
    # Ví dụ port_text = "8001", chưa phải số nguyên.
    port_text = os.getenv(
        "LLM_PORT", "8001"
    ).strip()

    # ------------------------------------------------
    # Kiểm tra API key
    # ------------------------------------------------

    if not api_key or api_key == "key_that_cua_may":
        raise ValueError(
            "GEMINI_API_KEY chưa được cấu hình hợp lệ"
        )

    # Hiện tại LLM_V1 mới hỗ trợ Gemini.
    # Sau này thêm Groq thì mở rộng điều kiện.
    if provider != "gemini":
        raise ValueError(
            f"Provider chưa được hỗ trợ: {provider}"
        )

    # ------------------------------------------------
    # Kiểm tra và chuyển kiểu port
    # ------------------------------------------------

    try:
        # int() chuyển chuỗi thành số nguyên.
        #
        # Ví dụ:
        # int("8001") -> 8001
        # int("abc") -> ValueError
        port = int(port_text)

    except ValueError as exc:
        # raise: phát sinh ngoại lệ.
        # from exc: giữ thông tin lỗi gốc.
        raise ValueError(
            "LLM_PORT phải là số nguyên"
        ) from exc

    # Port TCP hợp lệ nằm trong khoảng 1..65535.
    if not 1 <= port <= 65535:
        raise ValueError(
            "LLM_PORT phải nằm trong khoảng 1 đến 65535"
        )

    # ------------------------------------------------
    # Trả về đối tượng Settings
    # ------------------------------------------------

    return Settings(
        gemini_api_key=api_key,
        gemini_model=model,
        llm_provider=provider,
        llm_host=host,
        llm_port=port
    )

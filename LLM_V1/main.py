
"""
FILE: LLM_V1/main.py

MỤC ĐÍCH:
    Khởi chạy LLM Server bằng lệnh:
        python main.py

Cấu hình host và port được đọc từ .env.

Ví dụ:
    LLM_HOST=127.0.0.1
    LLM_PORT=8001
"""

# Thư viện chạy ứng dụng FastAPI.
import uvicorn

# Hàm get_settings() đã viết ở bước 5.
# Dùng để lấy cấu hình từ file .env.
from app.config import get_settings


if __name__ == "__main__":

    # Đọc các biến môi trường:
    #   GEMINI_API_KEY
    #   GEMINI_MODEL
    #   LLM_HOST
    #   LLM_PORT
    #
    # settings là một đối tượng của class Settings.
    settings = get_settings()

    # Khởi chạy LLM_V1 Server.
    #
    # "app.main:app":
    #   Import đối tượng FastAPI từ app/main.py.
    #
    # settings.llm_host:
    #   Địa chỉ server, lấy từ .env.
    #
    # settings.llm_port:
    #   Port server, lấy từ .env.
    #
    # reload=True:
    #   Tự khởi động lại khi sửa file Python.
    uvicorn.run(
        "app.main:app",
        host=settings.llm_host,
        port=settings.llm_port,
        reload=True
    )

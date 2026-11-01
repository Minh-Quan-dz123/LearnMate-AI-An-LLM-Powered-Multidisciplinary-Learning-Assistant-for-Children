# ============================================================
# FILE: app/llm_client.py
# PHỤ TRÁCH: THANH (THEO PHÂN CÔNG)
#
# MỤC ĐÍCH:
# Là thành phần giao tiếp HTTP giữa Backend và LLM Server.
#
# Module 1 và Module 2 dùng chung file này.
#
# File này KHÔNG xây dựng prompt nghiệp vụ.
# File này KHÔNG quyết định câu trả lời đúng hay sai.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - httpx:
#     Gửi HTTP request bất đồng bộ.
#
# - app.config.get_settings:
#     Lấy URL, timeout và cấu hình model.
#
# - typing:
#     Type hint nếu cần.

from typing import Any
import httpx 
from app.config import get_settings
GENERATE_PATH = "/internal/llm/generate" # endpoint cuar LLM Server
# 2. HÀM call_llm()
#
# Hàm đề xuất:
# async def call_llm(
#     task,
#     prompt,
#     model,
#     temperature,
#     max_output_tokens
# )
#
# Input:
# - task: str
#     Tên tác vụ LLM.
#
# - prompt: str
#     Nội dung prompt do EGM xây dựng.
#
# - model: str
#     Tên hoặc nhãn logic của model.
#
# - temperature: float
#     Tham số điều khiển tính ngẫu nhiên, nếu model hỗ trợ.
#
# - max_output_tokens: int
#     Giới hạn số token đầu ra.
#
# Output:
# - str: Nội dung text mà LLM tạo ra.
#
# TODO:
# Bước 1:
#     Đọc LLM_SERVER_URL và timeout từ Settings.
#
# Bước 2:
#     Tạo JSON request cho LLM Server.
#
# Bước 3:
#     Gửi POST /internal/llm/generate bằng HTTPX.
#
# Bước 4:
#     Kiểm tra HTTP status.
#
# Bước 5:
#     Đọc response JSON.
#
# Bước 6:
#     Kiểm tra success và data.content.
#
# Bước 7:
#     Trả về chuỗi content cho EGM xử lý tiếp.
#
# Request dự kiến:
# {
#   "task": "...",
#   "model": "...",
#   "prompt": "...",
#   "temperature": 0.5,
#   "max_output_tokens": 1800
# }
#
# Response dự kiến:
# {
#   "success": true,
#   "message": "Mô hình đã tạo nội dung",
#   "data": {
#     "content": "Nội dung LLM trả về"
#   }
# }


async def call_llm(
        task :str ,
        prompt: str ,
        model: str ,
        temperature: float = 0.5 ,
        max_output_tokens: int = 1800 ,
) -> str:
    #Bước 1 : đọc URL và timeout từ settings
    settings = get_settings()
    base_url = str(_setting(
        settings, ("LLM_SERVER_URL" , "llm_server_url") , "http://localhost:8001"
    )).rstrip("/")
    timeout = float(_setting(
        settings, ("LLM_TIMEOUT_SECONDS" , "llm_timeout_seconds" , "LLM_TIMEOUT" , "llm_timeout"), 60
    ))

    #Bước 2: tạo JSON request đúng contract với LLM Server
    payload = {
        "task" : task, 
        "model" : model,
        "prompt" : prompt ,
        "temperature" : temperature,
        "max_output_tokens": max_output_tokens,
    }

    #Bước 3 + 4 + 5 : gửi POST, kiếm tra HTTP status, đọc JSON
    #Không ghi log prompt hay header, thông báo lỗi chỉ chứa thông tin an toàn (mã lỗi)
    api_key = getattr(settings, "LLM_INTERNAL_API_KEY", None)
    headers = {"API key": api_key} if api_key else {} # sẽ chỉnh sửa khi biết được LLM Server đọc key ở header nào

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}{GENERATE_PATH}", json=payload, headers=headers
            )
            response.raise_for_status()
            body = response.json()
    except httpx.TimeoutException as e:
        raise LLMTimeoutError(f"LLM Server không phản hồi trong {timeout:g} giây") from e
    except httpx.ConnectError as e:
        raise LLMUnavailableError("Không kết nối được LLM Server") from e
    except httpx.HTTPStatusError as e :
        code = e.response.status_code 
        if code in (502, 503, 504):
            raise LLMUnavailableError(f"LLM Server không sẵn sàng (HTTP {code})") from e 
        raise LLMClientError(f"LLM Server trả lỗi HTTP {code}") from e
    except httpx.RequestError as e :
        raise LLMUnavailableError ("Lỗi mạng khi gọi LLM Server") from e 
    except ValueError as e : 
        raise LLMClientError ("LLM Server trả về dữ liệu không phải JSON") from e


    #Bước 6: kiểm tra success và data.content
    if not isinstance(body, dict) or body.get("success") is not True:
        raise LLMClientError("LLM Server báo xử lý không thành công")
    data = body.get("data")
    content = data.get("content") if isinstance(data, dict) else None
    if not isinstance(content,str) or not content.strip():
        raise LLMClientError("Phản hồi của LLM Server thiếu data.content")


    #Bước 7: trả chuỗi nội dung cho EGM xử lý tiêp
    return content

# 3. XỬ LÝ NGOẠI LỆ
#
# TODO:
# - Xử lý lỗi không kết nối được LLM Server.
# - Xử lý timeout.
# - Xử lý HTTP status không thành công.
# - Xử lý response thiếu data hoặc content.
# - Phân biệt lỗi timeout, unavailable và output không hợp lệ.
#
# Có thể tạo:
# - LLMClientError
# - LLMTimeoutError
# - LLMUnavailableError
#
# Router sẽ chuyển các lỗi này thành HTTP response thích hợp.


class LLMClientError(Exception):
    """Lỗi chung khi làm việc với LLM Server (lớp cha của mọi lỗi bên dưỡi)"""

class LLMTimeoutError(LLMClientError):
    """LLM Server không trả lời kịp thời gian cho phép"""

class LLMUnavailableError(LLMClientError):
    """Không kết nối được LLM Server (tắt, sau URL, mất mạng)"""

#hàm phụ :đọc cấu hình

def _setting(settings: Any, names : tuple[str, ...], default: Any ) -> Any:
    for name in names: 
        value = getattr(settings, name , None)
        if value not in (None , ""):
            return value 
        return default


# 4. QUY ƯỚC QUAN TRỌNG
#
# - Không tự tạo prompt trong file này.
# - Không parse schema bài trắc nghiệm trong file này.
# - Không đánh giá câu trả lời trong file này.
# - Không để lộ API Key trong log hoặc response.
# - Module 1 và 2 phải tái sử dụng cùng một hàm.
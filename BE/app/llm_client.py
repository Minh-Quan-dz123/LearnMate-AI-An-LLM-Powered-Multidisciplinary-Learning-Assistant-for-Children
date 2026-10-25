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


# 4. QUY ƯỚC QUAN TRỌNG
#
# - Không tự tạo prompt trong file này.
# - Không parse schema bài trắc nghiệm trong file này.
# - Không đánh giá câu trả lời trong file này.
# - Không để lộ API Key trong log hoặc response.
# - Module 1 và 2 phải tái sử dụng cùng một hàm.
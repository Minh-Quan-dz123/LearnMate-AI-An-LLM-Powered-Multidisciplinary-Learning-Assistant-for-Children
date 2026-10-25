# ============================================================
# FILE: scripts/try_llm.py
# PHỤ TRÁCH: THANH / QUÂN CÙNG KIỂM TRA
#
# MỤC ĐÍCH:
# Kiểm tra khả năng kết nối Backend với LLM Server
# mà không cần gọi API từ Frontend.
#
# Đây là script phục vụ thử nghiệm.
# Không phải thành phần nghiệp vụ chính.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - asyncio:
#     Chạy các hàm async trong script.
#
# - app.llm_client.call_llm:
#     Gọi LLM Server.
#
# - app.config.get_settings:
#     Lấy cấu hình model và URL nếu cần.


# 2. HÀM test_llm_connection()
#
# Mục đích:
# Kiểm tra một request đơn giản gửi đến LLM Server.
#
# Input:
# - Không có.
#
# Output:
# - In kết quả kiểm tra ra terminal.
#
# TODO:
# Bước 1:
#     Tạo một prompt thử nghiệm ngắn.
#
# Bước 2:
#     Gọi call_llm().
#
# Bước 3:
#     Nhận nội dung trả về.
#
# Bước 4:
#     In nội dung và trạng thái kiểm tra.
#
# Bước 5:
#     Nếu có lỗi, hiển thị loại lỗi dễ hiểu.
#
# Không in API Key hoặc secret.


# 3. HÀM main()
#
# TODO:
# - Gọi test_llm_connection().
# - Có thể bổ sung các bài thử nghiệm khác.
# - Sử dụng asyncio.run() để chạy hàm async.


# 4. CÁCH CHẠY
#
# Chạy tại thư mục gốc:
# python -m scripts.try_llm
#
# Lưu ý:
# Chỉ chạy được sau khi đã triển khai các hàm cần thiết.


# 5. KẾT QUẢ MONG ĐỢI
#
# - Gửi request thành công đến LLM Server.
# - Nhận được response hợp lệ.
# - Hiển thị nội dung model trả về.
# - Nhận diện được lỗi kết nối hoặc timeout.
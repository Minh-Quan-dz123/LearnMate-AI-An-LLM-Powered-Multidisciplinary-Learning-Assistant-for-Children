# ============================================================
# FILE: app/constants.py
# PHỤ TRÁCH: ____________
#
# MỤC ĐÍCH:
# Lưu các giá trị cố định sử dụng chung trong Backend.
# Tránh viết lặp lại các chuỗi nghiệp vụ.
# ============================================================


# 1. DANH SÁCH MÔN HỌC
#
# TODO:
# - Khai báo danh sách môn học được hỗ trợ.
#
# SUBJECTS:
# - "Khoa học tự nhiên"
# - "Đạo đức"
# - "Kỹ năng sống"


# 2. DANH SÁCH CHỦ ĐỀ
#
# TODO:
# - Khai báo SUBJECT_TOPICS.
# - Sử dụng dictionary ánh xạ môn học -> chủ đề.
#
# Ví dụ:
# "Khoa học tự nhiên":
#     - "Động vật và thực vật"
#     - "Cơ thể người"
#     - "Môi trường và tài nguyên thiên nhiên"
#     - "Vật chất và năng lượng"
#     - "Trái Đất và bầu trời"
#
# Có thể bổ sung các chủ đề còn lại từ tài liệu thiết kế.
# Cho phép FE truyền chủ đề tự nhập theo API contract.


# 3. MỨC ĐỘ BÀI TẬP
#
# TODO:
# - Khai báo SUPPORTED_LEVELS.
#
# Giá trị:
# - "Cơ bản"
# - "Nâng cao"


# 4. LOẠI CÂU HỎI
#
# TODO:
# - Khai báo QUESTION_TYPES.
#
# Giá trị:
# - "Trắc nghiệm một đáp án"
# - "Trắc nghiệm nhiều đáp án"
# - "Câu trả lời mở"


# 5. GIỚI HẠN BÀI TẬP
#
# TODO:
# - MIN_QUESTION_COUNT = 1
# - MAX_QUESTION_COUNT = 5
#
# Các module phải sử dụng cùng giới hạn này.


# 6. GIỚI HẠN TUỔI
#
# TODO:
# - Khai báo giới hạn tuổi theo contract.
# - Giá trị minh họa trong thiết kế là 3 đến 15.
#
# Sử dụng khi kiểm tra hồ sơ trẻ.


# 7. CÁC HẰNG SỐ KHÁC
#
# TODO:
# - Có thể bổ sung mã lỗi hoặc hằng số cần dùng chung.
# - Chỉ thêm khi thực sự có nhu cầu.
# - Không chứa cấu hình bí mật hay prompt dài trong file này.
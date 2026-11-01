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


SUBJECTS = [
    "Khoa học tự nhiên",
    "Đạo đức",
    "Kỹ năng sống",
]

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

# Đây chỉ là danh sách GỢI Ý. FE cho phép user tự nhập chủ đề (hoặc chọn
# "Random"), nên schema KHÔNG ép topic phải nằm trong danh sách này.
SUBJECT_TOPICS = {
    "Khoa học tự nhiên": [
        "Động vật và thực vật",
        "Cơ thể người",
        "Môi trường và tài nguyên thiên nhiên",
        "Vật chất và năng lượng",
        "Trái Đất và bầu trời",
    ],
    "Đạo đức": [
        "Yêu thương gia đình",
        "Kính trọng thầy cô, lễ phép với người lớn",
        "Đoàn kết, giúp đỡ bạn bè",
        "Trung thực",
        "Chăm chỉ, có trách nhiệm",
        "Tuân thủ quy định nơi công cộng",
        "Bảo vệ của công",
    ],
    "Kỹ năng sống": [
        "Kỹ năng giao tiếp",
        "Kỹ năng quản lý cảm xúc",
        "Kỹ năng tự phục vụ",
        "Kỹ năng làm việc nhóm",
        "Kỹ năng giải quyết vấn đề",
        "Kỹ năng tự bảo vệ bản thân",
        "Kỹ năng xử lý tình huống nguy hiểm",
    ],
}

# 3. MỨC ĐỘ BÀI TẬP
#
# TODO:
# - Khai báo SUPPORTED_LEVELS.
#
# Giá trị:
# - "Cơ bản"
# - "Nâng cao"

SUPPORTED_LEVELS = ["Cơ bản", "Nâng cao"]

# 4. LOẠI CÂU HỎI
#
# TODO:
# - Khai báo QUESTION_TYPES.
#
# Giá trị:
# - "Trắc nghiệm một đáp án"
# - "Trắc nghiệm nhiều đáp án"
# - "Câu trả lời mở"

QUESTION_TYPES = [
    "Trắc nghiệm một đáp án",
    "Trắc nghiệm nhiều đáp án",
    "Câu trả lời mở",
]

# 5. GIỚI HẠN BÀI TẬP
#
# TODO:
# - MIN_QUESTION_COUNT = 1
# - MAX_QUESTION_COUNT = 5
#
# Các module phải sử dụng cùng giới hạn này.

MIN_QUESTION_COUNT = 1
MAX_QUESTION_COUNT = 5

# 6. GIỚI HẠN TUỔI
#
# TODO:
# - Khai báo giới hạn tuổi theo contract.
# - Giá trị minh họa trong thiết kế là 3 đến 15.
#
# Sử dụng khi kiểm tra hồ sơ trẻ.

MIN_CHILD_AGE = 3
MAX_CHILD_AGE = 15

# 7. CÁC HẰNG SỐ KHÁC
#
# TODO:
# - Có thể bổ sung mã lỗi hoặc hằng số cần dùng chung.
# - Chỉ thêm khi thực sự có nhu cầu.
# - Không chứa cấu hình bí mật hay prompt dài trong file này.



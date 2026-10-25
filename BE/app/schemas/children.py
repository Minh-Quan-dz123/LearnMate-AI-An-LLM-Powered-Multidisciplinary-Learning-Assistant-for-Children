# ============================================================
# FILE: app/schemas/children.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Định nghĩa dữ liệu dùng để tạo, đọc, sửa, xóa hồ sơ trẻ.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel
# - pydantic.Field
# - typing / kiểu dữ liệu chuẩn Python khi cần.


# 2. CLASS CreateChildRequest
#
# Các trường:
# - user_id: int
# - name: str
# - age: int
# - gender: str | None
# - interests: list[str]
#
# TODO:
# - Kiểm tra user_id là số nguyên dương.
# - Kiểm tra name không rỗng.
# - Kiểm tra tuổi nằm trong giới hạn thống nhất.
# - Cho phép gender không được cung cấp.
# - interests mặc định là danh sách rỗng.
#
# Lưu ý:
# Dùng default_factory cho danh sách nếu cần.


# 3. CLASS UpdateChildRequest
#
# Các trường:
# - user_id: int
# - name: str
# - age: int
# - gender: str | None
# - interests: list[str]
#
# TODO:
# - Định nghĩa dữ liệu cập nhật hồ sơ.
# - Theo contract PUT hiện tại, FE gửi dữ liệu hồ sơ đầy đủ.
# - Nếu chọn cập nhật một phần thì phải thống nhất lại contract.


# 4. CLASS ChildData
#
# Dữ liệu hồ sơ trả về Frontend:
#
# - child_id: int
# - name: str
# - age: int
# - gender: str | None
# - interests: list[str]
#
# Lưu ý:
# - Database sử dụng cột id.
# - API có thể trả về tên child_id.
# - Cần ánh xạ giữa hai tên khi tạo response.


# 5. CLASS ChildResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: ChildData


# 6. CLASS ChildrenResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: list[ChildData]
#
# Dùng cho API lấy danh sách hồ sơ trẻ.


# 7. CLASS DeleteChildResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: None
#
# Dùng cho API xóa hồ sơ thành công.


# 8. KIỂM TRA
#
# TODO:
# - Hồ sơ hợp lệ.
# - Thiếu tên.
# - Tuổi không hợp lệ.
# - Danh sách sở thích rỗng.
# - Giới tính không được cung cấp.
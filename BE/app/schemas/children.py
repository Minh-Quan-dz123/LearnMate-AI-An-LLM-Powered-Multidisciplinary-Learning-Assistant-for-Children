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


from pydantic import BaseModel, Field, field_validator

# 1. CÁC TRƯỜNG DỮ LIỆU CHUNG
class ChildBase(BaseModel):

    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=2, le=15)
    gender: str|None = Field(default=None, max_length=60)
    interests: list[str] = Field(default_factory=list)

    # kiểm tra tên ko để trống
    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Tên trẻ không được để trống")

        return value


# 2. REQUEST TẠO HỒ SƠ
class CreateChildRequest(ChildBase):

    # thêm id của user
    user_id: int = Field(gt=0)

# 3. REQUEST CẬP NHẬT HỒ SƠ
class UpdateChildRequest(CreateChildRequest):

    # giống class số 2
    pass
# pass là câu lệnh không thực hiện bất kỳ hành động nào. 
# Nó được dùng khi cú pháp yêu cầu phải có một câu lệnh, 
# nhưng bạn không muốn viết thêm gì.

# =============== RESPONSE ===================

# 4. DỮ LIỆU HỒ SƠ TRẢ VỀ FRONTEND
class ChildData(ChildBase):
    child_id: int

# 5. RESPONSE MỘT HỒ SƠ
class ChildResponse(BaseModel):
    success: bool
    message: str
    data: ChildData


# 6. RESPONSE DANH SÁCH HỒ SƠ
class ChildrenListResponse(BaseModel):
    success: bool
    message: str
    data: list[ChildData]

# 7. RESPONSE XÓA HỒ SƠ
class DeleteChildResponse(BaseModel):
    success: bool
    message: str
    data: None = None


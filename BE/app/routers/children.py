# ============================================================
# FILE: app/routers/children.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Quản lý hồ sơ trẻ thuộc một tài khoản.
#
# Chức năng:
# - Tạo hồ sơ.
# - Lấy danh sách.
# - Lấy chi tiết.
# - Cập nhật.
# - Xóa.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - fastapi.Query
# - fastapi.Path
# - app.database.get_supabase
# - app.schemas.children:
#     CreateChildRequest, UpdateChildRequest,
#     ChildData, ChildResponse,
#     ChildrenResponse, DeleteChildResponse
#
# Khởi tạo router với prefix="/api/children".


# 2. HÀM create_child()
#
# Endpoint:
# POST /api/children
#
# Input:
# - CreateChildRequest
#
# Output:
# - ChildResponse
#
# TODO:
# Bước 1: Nhận dữ liệu hồ sơ trẻ.
# Bước 2: Kiểm tra user_id tồn tại.
# Bước 3: Kiểm tra name, age và các trường khác.
# Bước 4: Thêm bản ghi vào child_profiles.
# Bước 5: Lấy id hồ sơ vừa tạo.
# Bước 6: Chuyển id thành child_id trong API response.
# Bước 7: Trả HTTP 201.


# 3. HÀM list_children()
#
# Endpoint:
# GET /api/children?user_id=1
#
# Input:
# - user_id: int, query parameter
#
# Output:
# - ChildrenResponse
#
# TODO:
# Bước 1: Nhận user_id.
# Bước 2: Truy vấn child_profiles theo user_id.
# Bước 3: Chuyển các bản ghi thành ChildData.
# Bước 4: Trả danh sách hồ sơ.
#
# Nếu không có hồ sơ:
# - Trả danh sách rỗng.
# - Không coi đây là lỗi.


# 4. HÀM get_child()
#
# Endpoint:
# GET /api/children/{child_id}?user_id=1
#
# Input:
# - child_id: int, path parameter
# - user_id: int, query parameter
#
# Output:
# - ChildResponse
#
# TODO:
# Bước 1: Nhận child_id và user_id.
# Bước 2: Truy vấn hồ sơ khớp cả hai ID.
# Bước 3: Nếu không tìm thấy, trả HTTP 404.
# Bước 4: Trả dữ liệu hồ sơ.


# 5. HÀM update_child()
#
# Endpoint:
# PUT /api/children/{child_id}
#
# Input:
# - child_id: int, path parameter
# - UpdateChildRequest, JSON body
#
# Output:
# - ChildResponse
#
# TODO:
# Bước 1: Nhận dữ liệu cập nhật.
# Bước 2: Kiểm tra hồ sơ thuộc user_id được gửi.
# Bước 3: Kiểm tra dữ liệu hợp lệ.
# Bước 4: Cập nhật trong bảng child_profiles.
# Bước 5: Trả hồ sơ sau cập nhật.
#
# Lưu ý:
# - Không tự ý tạo hồ sơ mới nếu child_id không tồn tại.


# 6. HÀM delete_child()
#
# Endpoint:
# DELETE /api/children/{child_id}?user_id=1
#
# Input:
# - child_id: int
# - user_id: int
#
# Output:
# - DeleteChildResponse
#
# TODO:
# Bước 1: Nhận child_id và user_id.
# Bước 2: Kiểm tra hồ sơ khớp hai ID.
# Bước 3: Nếu không tồn tại, trả HTTP 404.
# Bước 4: Xóa hồ sơ khỏi Database.
# Bước 5: Trả thông báo xóa thành công.


# 7. LƯU Ý CHUNG
#
# - user_id dùng để xác định dữ liệu demo.
# - Việc gửi user_id không phải cơ chế xác thực an toàn.
# - Không được coi hệ thống này đã có phân quyền production.
# - Không lưu bài tập vào bảng child_profiles.
#
# Các endpoint cần thống nhất với FE về user_id
# được gửi trong query hay JSON body.


# 8. KIỂM TRA
#
# TODO:
# - Tạo hồ sơ hợp lệ.
# - Tạo hồ sơ với user_id không tồn tại.
# - Lấy danh sách nhiều hồ sơ.
# - Cập nhật đúng hồ sơ.
# - Cập nhật hồ sơ không thuộc user_id.
# - Xóa hồ sơ.
# - Xóa hồ sơ không tồn tại.
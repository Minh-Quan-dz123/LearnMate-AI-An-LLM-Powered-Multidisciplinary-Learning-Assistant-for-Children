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

# 1. IMPORT THƯ VIỆN

import logging

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse

from supabase import AsyncClient
from postgrest.exceptions import APIError

from app.database import get_supabase

from app.schemas.children import (
    CreateChildRequest,
    UpdateChildRequest,
    ChildData,
    ChildResponse,
    ChildrenListResponse,
    DeleteChildResponse,
)

# 2. KHỞI TẠO ROUTER
router = APIRouter(
    prefix="/api/children",
    tags=["Children"]
)

logger = logging.getLogger(__name__)

# 3. HÀM TRẢ RESPONSE LỖI
def error_response(status_code: int, message: str, code: str) -> JSONResponse:

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": {
                "code": code,
                "details": None
            }
        }
    )

# 4. HÀM CHUYỂN DỮ LIỆU DATABASE SANG SCHEMA
def to_child_data(child: dict) -> ChildData:

    return ChildData(
        child_id=child["id"],
        name=child["name"],
        age=child["age"],
        gender=child["gender"],
        interests=child["interests"] or []
    )


# 5. TẠO HỒ SƠ TRẺ
# POST /api/children
@router.post("", response_model=ChildResponse,status_code=201)
async def create_child(request: CreateChildRequest, db: AsyncClient = Depends(get_supabase)):
    """
    Tạo hồ sơ trẻ mới.

    Input:
        request: CreateChildRequest
        db: Supabase AsyncClient

    Output:
        ChildResponse

    Quy trình:
        1. Kiểm tra user_id tồn tại.
        2. Thêm hồ sơ vào child_profiles.
        3. Lấy thông tin hồ sơ vừa tạo.
        4. Trả response thành công.
    """

    try:
        # BƯỚC 1: KIỂM TRA USER TỒN TẠI
        user_result = await (
            db.table("users")
            .select("id")
            .eq("id", request.user_id)
            .limit(1)
            .execute()
        )

        if not user_result.data:
            return error_response(
                404,
                "Tài khoản không tồn tại",
                "USER_NOT_FOUND"
            )

        # BƯỚC 2: THÊM HỒ SƠ TRẺ
        result = await (
            db.table("child_profiles")
            .insert({
                "user_id": request.user_id,
                "name": request.name,
                "age": request.age,
                "gender": request.gender,
                "interests": request.interests
            })
            .select(
                "id, name, age, gender, interests"
            )
            .execute() 
        )
        print("INSERT RESULT:", result.data)

        # BƯỚC 3: KIỂM TRA INSERT
        if not result.data:
            return error_response(
                503,
                "Không thể tạo hồ sơ trẻ",
                "DATABASE_ERROR"
            )

        # BƯỚC 4: LẤY HỒ SƠ VỪA TẠO
        child = result.data[0]

        # BƯỚC 5: TRẢ RESPONSE
        return ChildResponse(
            success=True,
            message="Tạo hồ sơ trẻ thành công",
            data=ChildData(
                child_id=child["id"],
                name=child["name"],
                age=child["age"],
                gender=child["gender"],
                interests=child["interests"]
            )
        )

    # XỬ LÝ LỖI DATABASE
    except APIError as exc:

        print("SUPABASE ERROR:", str(exc))
        print("ERROR CODE:", exc.code)


        # Vi phạm FOREIGN KEY
        if exc.code == "23503":
            return error_response(
                404,
                "Tài khoản không tồn tại",
                "USER_NOT_FOUND"
            )

        return error_response(
            503,
            "Không thể truy cập cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    # XỬ LÝ LỖI KHÔNG MONG ĐỢI
    except Exception:
        logger.exception("Unexpected error in create_child")

        return error_response(
            500,
            "Đã xảy ra lỗi khi tạo hồ sơ",
            "INTERNAL_ERROR"
        )


# 6. LẤY DANH SÁCH HỒ SƠ TRẺ
# GET /api/children?user_id=1
@router.get("", response_model=ChildrenListResponse, status_code=200)
async def get_children(user_id: int = Query(gt=0), db: AsyncClient = Depends(get_supabase)):

    """
    Lấy danh sách hồ sơ trẻ của một tài khoản.

    Input:
        user_id: ID của tài khoản.
        db: Supabase AsyncClient.

    Output:
        ChildrenListResponse.
    """

    try:
        # BƯỚC 1: TRUY VẤN DATABASE
        result = await (
            db.table("child_profiles")
            .select("id, name, age, gender, interests")
            .eq("user_id", user_id)
            .order("id")
            .execute()
        )

        # BƯỚC 2: CHUYỂN DỮ LIỆU THÀNH CHILD DATA
        children = [
            ChildData(
                child_id=child["id"],
                name=child["name"],
                age=child["age"],
                gender=child["gender"],
                interests=child["interests"]
            )
            for child in result.data
        ]

        # BƯỚC 3: TRẢ RESPONSE
        return ChildrenListResponse(
            success=True,
            message="Lấy danh sách hồ sơ thành công",
            data=children
        )

    except APIError as exc:
        print("SUPABASE ERROR:", str(exc))

        return error_response(
            503,
            "Không thể truy cập cơ sở dữ liệu",
            "DATABASE_ERROR"
        )


# 7. LẤY CHI TIẾT MỘT HỒ SƠ
# GET /api/children/{child_id}?user_id=1
@router.get("/{child_id}", response_model=ChildResponse,status_code=200)
async def get_child(
    child_id: int = Path(gt=0),
    user_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase)
):

    try:
        # B1: Tìm hồ sơ theo child_id và user_id
        result = await (
            db.table("child_profiles")
            .select("id, name, age, gender, interests")
            .eq("id", child_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        # B2: Kiểm tra hồ sơ
        if not result.data:
            return error_response(
                404,
                "Không tìm thấy hồ sơ trẻ",
                "CHILD_NOT_FOUND"
            )

        # B3: Trả response
        return ChildResponse(
            success=True,
            message="Lấy thông tin hồ sơ thành công",
            data=to_child_data(result.data[0])
        )

    except APIError as exc:
        logger.error("Supabase get_child: %s", exc)

        return error_response(
            503,
            "Không thể truy cập cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    except Exception:
        logger.exception("Unexpected error in get_child")

        return error_response(
            500,
            "Đã xảy ra lỗi khi lấy hồ sơ",
            "INTERNAL_ERROR"
        )


# 8. CẬP NHẬT HỒ SƠ TRẺ
# PUT /api/children/{child_id}
@router.put("/{child_id}", response_model=ChildResponse, status_code=200)
async def update_child(
    request: UpdateChildRequest,
    child_id: int = Path(gt=0),
    db: AsyncClient = Depends(get_supabase)
):

    try:
        # B1: Cập nhật hồ sơ
        result = await (
            db.table("child_profiles")
            .update({
                "name": request.name,
                "age": request.age,
                "gender": request.gender,
                "interests": request.interests
            })
            .eq("id", child_id)
            .eq("user_id", request.user_id)
            .select("id, name, age, gender, interests")
            .execute()
        )

        # B2: Kiểm tra hồ sơ tồn tại
        if not result.data:
            return error_response(
                404,
                "Không tìm thấy hồ sơ trẻ",
                "CHILD_NOT_FOUND"
            )

        # B3: Trả response
        return ChildResponse(
            success=True,
            message="Cập nhật hồ sơ thành công",
            data=to_child_data(result.data[0])
        )

    except APIError as exc:
        logger.error("Supabase update_child: %s", exc)

        return error_response(
            503,
            "Không thể cập nhật cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    except Exception:
        logger.exception("Unexpected error in update_child")

        return error_response(
            500,
            "Đã xảy ra lỗi khi cập nhật hồ sơ",
            "INTERNAL_ERROR"
        )


# 9. XÓA HỒ SƠ TRẺ
# DELETE /api/children/{child_id}?user_id=1
@router.delete("/{child_id}", response_model=DeleteChildResponse,status_code=200)
async def delete_child(
    child_id: int = Path(gt=0),
    user_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase)
):

    try:
        # B1: Xóa hồ sơ theo child_id và user_id
        result = await (
            db.table("child_profiles")
            .delete()
            .eq("id", child_id)
            .eq("user_id", user_id)
            .select("id")
            .execute()
        )

        # B2: Kiểm tra có bản ghi được xóa không
        if not result.data:
            return error_response(
                404,
                "Không tìm thấy hồ sơ trẻ",
                "CHILD_NOT_FOUND"
            )

        # B3: Trả response
        return DeleteChildResponse(
            success=True,
            message="Đã xóa hồ sơ trẻ",
            data=None
        )

    except APIError as exc:
        logger.error("Supabase delete_child: %s", exc)

        return error_response(
            503,
            "Không thể xóa hồ sơ trong cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    except Exception:
        logger.exception("Unexpected error in delete_child")

        return error_response(
            500,
            "Đã xảy ra lỗi khi xóa hồ sơ",
            "INTERNAL_ERROR"
        )

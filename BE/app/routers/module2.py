# ============================================================
# FILE: app/routers/module2.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Cung cấp hai API:
# - Sinh câu hỏi mở.
# - Đánh giá câu trả lời của trẻ.
# ============================================================


"""
FILE: app/routers/module2.py

Module 2 - Câu trả lời mở.

Cung cấp hai API:
    POST /api/exercises/open/generate
    POST /api/exercises/open/evaluate

Router chỉ nhận request, lấy tuổi từ Supabase,
gọi EGM và trả response cho Frontend.

Prompt và việc kiểm tra đầu ra LLM được xử lý
tại app/egm/module2_egm.py.
"""

# ============================================================
# 1. IMPORT THƯ VIỆN
# ============================================================

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from supabase import AsyncClient

from app.database import get_supabase

from app.egm.module2_egm import (
    LLMOutputError,
    evaluate_open_answer as egm_evaluate_open_answer,
    generate_open_questions as egm_generate_open_questions,
)

from app.llm_client import (
    LLMClientError,
    LLMTimeoutError,
    LLMUnavailableError,
)

from app.schemas.module2 import (
    OpenEvaluateRequest,
    OpenEvaluateResponse,
    OpenGenerateRequest,
    OpenGenerateResponse,
)


# ============================================================
# 2. KHỞI TẠO ROUTER
# ============================================================

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/exercises/open",
    tags=["Module 2 - Bài tập mở"],
)


# ============================================================
# 3. ĐỊNH NGHĨA LỖI HỒ SƠ TRẺ
# ============================================================

class ChildProfileError(Exception):
    """
    Lỗi nghiệp vụ khi truy vấn hồ sơ trẻ.

    Input:
        status_code: HTTP status
        code: Mã lỗi
        message: Thông báo tiếng Việt

    Mục đích:
        - Phân biệt lỗi hồ sơ với lỗi LLM.
        - Không trả lỗi Database thô cho Frontend.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str
    ):
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.message = message


# ============================================================
# 4. HÀM TRẢ RESPONSE LỖI
# ============================================================

def _error_response(
    status_code: int,
    code: str,
    message: str
) -> JSONResponse:
    """
    Chuẩn hóa response lỗi theo API contract.

    Ví dụ:
        _error_response(
            404,
            "CHILD_NOT_FOUND",
            "Không tìm thấy hồ sơ trẻ."
        )

    Output:
        {
            "success": false,
            "message": "...",
            "error": {
                "code": "...",
                "details": null
            }
        }

    Sử dụng JSONResponse để không bị FastAPI
    bọc thêm một lớp "detail".
    """

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


# ============================================================
# 5. HÀM CHUYỂN LỖI LLM THÀNH HTTP RESPONSE
# ============================================================

def _llm_error_response(
    exc: LLMClientError
) -> JSONResponse:
    """
    Chuyển lỗi từ LLM Server thành HTTP response.

    Các trường hợp:
        LLMOutputError      -> HTTP 502
        LLMTimeoutError     -> HTTP 504
        LLMUnavailableError -> HTTP 503
        LLMClientError      -> HTTP 502

    Không trả trực tiếp str(exc) để tránh lộ
    nội dung không phù hợp từ LLM Server.
    """

    # Trường hợp 1: Model trả dữ liệu sai định dạng.
    if isinstance(exc, LLMOutputError):
        return _error_response(
            502,
            "INVALID_MODEL_OUTPUT",
            "AI chưa tạo được kết quả hợp lệ. Vui lòng thử lại."
        )

    # Trường hợp 2: LLM Server phản hồi quá lâu.
    if isinstance(exc, LLMTimeoutError):
        return _error_response(
            504,
            "LLM_TIMEOUT",
            "Hệ thống AI phản hồi quá chậm. Vui lòng thử lại."
        )

    # Trường hợp 3: Không kết nối được LLM Server.
    if isinstance(exc, LLMUnavailableError):
        return _error_response(
            503,
            "LLM_UNAVAILABLE",
            "Hệ thống AI tạm thời không khả dụng. Vui lòng thử lại."
        )

    # Trường hợp 4: Các lỗi LLM khác.
    return _error_response(
        502,
        "LLM_ERROR",
        "Không thể xử lý dữ liệu từ hệ thống AI. Vui lòng thử lại."
    )


# ============================================================
# 6. HÀM LẤY TUỔI TRẺ TỪ SUPABASE
# ============================================================

async def _get_child_profile(
    child_id: int,
    db: AsyncClient
) -> dict:
    """
    Truy vấn tuổi của trẻ dựa trên child_id.

    Input:
        child_id: ID hồ sơ trẻ
        db: Supabase AsyncClient

    Output:
        age: Tuổi của trẻ (int)

    Các bước:
        1. Truy vấn bảng child_profiles.
        2. Tìm hồ sơ theo id.
        3. Kiểm tra hồ sơ tồn tại.
        4. Kiểm tra tuổi nằm trong [3, 15].
        5. Trả về tuổi.

    Ví dụ:
        child_id = 101

        Database:
            {
                "id": 101,
                "name": "Bé An",
                "age": 7
            }

        Output:
            7
    """

    # --------------------------------------------------------
    # BƯỚC 1: TRUY VẤN DATABASE
    # --------------------------------------------------------

    try:
        result = await (
            db.table("child_profiles")
            .select("id, age, gender, interests")
            .eq("id", child_id)
            .limit(1)
            .execute()
        )

    except Exception as exc:

        logger.exception(
            "Module 2: không truy vấn được bảng child_profiles"
        )

        raise ChildProfileError(
            503,
            "DATABASE_ERROR",
            "Không thể truy cập cơ sở dữ liệu."
        ) from exc

    # --------------------------------------------------------
    # BƯỚC 2: LẤY DỮ LIỆU TRẢ VỀ
    # --------------------------------------------------------

    rows = result.data or []

    # --------------------------------------------------------
    # BƯỚC 3: KIỂM TRA HỒ SƠ CÓ TỒN TẠI KHÔNG
    # --------------------------------------------------------

    if not rows:
        raise ChildProfileError(
            404,
            "CHILD_NOT_FOUND",
            "Không tìm thấy hồ sơ trẻ."
        )

    # --------------------------------------------------------
    # BƯỚC 4: LẤY THÔNG TIN HỒ SƠ TRẺ
    # --------------------------------------------------------

    # Lấy bản ghi hồ sơ đầu tiên từ kết quả Supabase.
    profile = rows[0]

    # Lấy tuổi của trẻ.
    age = profile.get("age")

    # Kiểm tra tuổi hợp lệ trong khoảng 3 đến 15.
    if type(age) is not int or not 3 <= age <= 15:
        raise ChildProfileError(
            422,
            "INVALID_CHILD_AGE",
            "Tuổi trong hồ sơ trẻ không hợp lệ."
        )

    # --------------------------------------------------------
    # BƯỚC 5: LẤY GIỚI TÍNH
    # --------------------------------------------------------

    # Lấy gender từ Database.
    raw_gender = profile.get("gender")

    # Nếu giới tính là chuỗi, loại bỏ khoảng trắng.
    # Nếu NULL hoặc không hợp lệ, sử dụng None.
    gender = (
        (raw_gender.strip() or None)
        if isinstance(raw_gender, str)
        else None
    )

    # --------------------------------------------------------
    # BƯỚC 6: LẤY DANH SÁCH SỞ THÍCH
    # --------------------------------------------------------

    # Lấy interests từ Database.
    raw_interests = profile.get("interests")

    # Chỉ giữ các sở thích hợp lệ.
    if isinstance(raw_interests, list):
        interests = [
            item.strip()
            for item in raw_interests
            if isinstance(item, str) and item.strip()
        ]
    else:
        interests = []

    # --------------------------------------------------------
    # BƯỚC 7: TRẢ VỀ THÔNG TIN HỒ SƠ
    # --------------------------------------------------------

    return {
        "age": age,
        "gender": gender,
        "interests": interests
    }


# ============================================================
# 7. API SINH CÂU HỎI MỞ
# ============================================================

@router.post(
    "/generate",
    response_model=OpenGenerateResponse,
    status_code=200
)
async def generate_open_questions(
    request: OpenGenerateRequest,
    db: AsyncClient = Depends(get_supabase)
):
    """
    Endpoint:
        POST /api/exercises/open/generate

    Input:
        OpenGenerateRequest

    Output:
        OpenGenerateResponse

    Chức năng:
        Sinh 1-5 câu hỏi mở theo cấu hình.

    Quy trình:
        1. FastAPI/Pydantic kiểm tra request.
        2. Lấy tuổi trẻ từ Database.
        3. Gọi EGM sinh câu hỏi.
        4. EGM gọi LLM Server.
        5. EGM kiểm tra dữ liệu LLM trả về.
        6. Trả danh sách câu hỏi cho Frontend.
    """

    # --------------------------------------------------------
    # BƯỚC 1: VALIDATE REQUEST
    # --------------------------------------------------------

    # FastAPI và Pydantic tự kiểm tra:
    # - child_id > 0
    # - subject hợp lệ
    # - topic không rỗng
    # - level hợp lệ
    # - question_type = "Câu trả lời mở"
    # - question_count từ 1 đến 5

    # --------------------------------------------------------
    # BƯỚC 2: LẤY TUỔI CỦA TRẺ
    # --------------------------------------------------------

    try:
        profile = await _get_child_profile(
            child_id=request.child_id,
            db=db
        )

    except ChildProfileError as exc:
        return _error_response(
            exc.status_code,
            exc.code,
            exc.message
        )

    # --------------------------------------------------------
    # BƯỚC 3: GỌI EGM SINH CÂU HỎI MỞ
    # --------------------------------------------------------

    try:
        exercise = await egm_generate_open_questions(
            request=request,
            age=profile["age"],
            gender=profile["gender"],
            interests=profile["interests"],
        )

    # --------------------------------------------------------
    # BƯỚC 4: XỬ LÝ LỖI LLM
    # --------------------------------------------------------

    except LLMClientError as exc:

        logger.warning(
            "Module 2 generate: %s",
            type(exc).__name__
        )

        return _llm_error_response(exc)

    # --------------------------------------------------------
    # BƯỚC 5: TRẢ KẾT QUẢ CHO FRONTEND
    # --------------------------------------------------------

    return OpenGenerateResponse(
        success=True,
        message="Tạo câu hỏi thành công",
        data=exercise
    )


# ============================================================
# 8. API ĐÁNH GIÁ CÂU TRẢ LỜI MỞ
# ============================================================

@router.post(
    "/evaluate",
    response_model=OpenEvaluateResponse,
    status_code=200
)
async def evaluate_open_answer(
    request: OpenEvaluateRequest,
    db: AsyncClient = Depends(get_supabase)
):
    """
    Endpoint:
        POST /api/exercises/open/evaluate

    Input:
        OpenEvaluateRequest

    Output:
        OpenEvaluateResponse

    Chức năng:
        Đánh giá một câu trả lời mở của trẻ.

    Quy trình:
        1. FastAPI/Pydantic kiểm tra request.
        2. Kiểm tra câu trả lời không rỗng.
        3. Lấy tuổi trẻ từ Database.
        4. Gọi EGM đánh giá.
        5. EGM gửi prompt tới LLM Server.
        6. EGM validate kết quả đánh giá.
        7. Trả điểm và nhận xét cho Frontend.
    """

    # --------------------------------------------------------
    # BƯỚC 1: VALIDATE REQUEST
    # --------------------------------------------------------

    # Pydantic tự kiểm tra:
    # - child_id hợp lệ
    # - question_id không rỗng
    # - question không rỗng
    # - answer không rỗng (kể cả toàn dấu cách)
    # - evaluation_criteria hợp lệ
    # - level hợp lệ

    # --------------------------------------------------------
    # BƯỚC 2: LẤY TUỔI CỦA TRẺ
    # --------------------------------------------------------

    try:
        profile = await _get_child_profile(
            child_id=request.child_id,
            db=db
        )

    except ChildProfileError as exc:
        return _error_response(
            exc.status_code,
            exc.code,
            exc.message
        )

    # --------------------------------------------------------
    # BƯỚC 3: GỌI EGM ĐÁNH GIÁ CÂU TRẢ LỜI
    # --------------------------------------------------------

    try:
        evaluation = await egm_evaluate_open_answer(
            request=request,
            age=profile["age"],
            gender=profile["gender"],
            interests=profile["interests"],
        )

    # --------------------------------------------------------
    # BƯỚC 4: XỬ LÝ LỖI LLM
    # --------------------------------------------------------

    except LLMClientError as exc:

        logger.warning(
            "Module 2 evaluate: %s",
            type(exc).__name__
        )

        return _llm_error_response(exc)

    # --------------------------------------------------------
    # BƯỚC 5: TRẢ KẾT QUẢ CHO FRONTEND
    # --------------------------------------------------------

    return OpenEvaluateResponse(
        success=True,
        message="Đã đánh giá câu trả lời",
        data=evaluation
    )

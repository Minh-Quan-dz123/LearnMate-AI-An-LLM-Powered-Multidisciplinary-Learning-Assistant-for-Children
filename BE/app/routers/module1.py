# ============================================================
# FILE: app/routers/module1.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Cung cấp API sinh bài tập trắc nghiệm.
#
# Module 1 chỉ sinh câu hỏi.
# Frontend tự chấm điểm dựa trên correct_option_ids.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - app.database.get_supabase
# - app.schemas.module1:
#     QuizGenerateRequest, QuizGenerateResponse
# - app.egm.module1_egm.generate_quiz
#
# Khởi tạo router với prefix="/api/exercises/quiz".


# 2. HÀM generate_quiz()
#
# Endpoint:
# POST /api/exercises/quiz/generate
#
# Input:
# - QuizGenerateRequest
#
# Output:
# - QuizGenerateResponse
#
# TODO:
# Bước 1:
#     Nhận cấu hình bài tập từ FE.
#
# Bước 2:
#     Kiểm tra request bằng Pydantic.
#
# Bước 3:
#     Truy vấn child_profiles theo child_id.
#
# Bước 4:
#     Nếu hồ sơ không tồn tại, trả HTTP 404.
#
# Bước 5:
#     Lấy age và các sở thích cần thiết của trẻ.
#
# Bước 6:
#     Gọi generate_quiz() trong module1_egm.py.
#     Truyền vào cấu hình bài và thông tin phù hợp của trẻ.
#
# Bước 7:
#     Nhận dữ liệu bài tập đã được EGM kiểm tra.
#
# Bước 8:
#     Đóng gói thành QuizGenerateResponse.
#
# Bước 9:
#     Trả HTTP 200 cho FE.


# 3. XỬ LÝ LỖI
#
# TODO:
# - child_id không tồn tại -> 404.
# - question_count không hợp lệ -> 422.
# - Request không hợp lệ -> 422.
# - Model output sai schema -> 502.
# - LLM Server không khả dụng -> 503.
# - LLM Server timeout -> 504.


# 4. QUY ƯỚC
#
# - Không viết prompt trực tiếp trong Router.
# - Không gửi HTTP request trực tiếp đến LLM Server.
# - Không tự parse JSON do LLM sinh trong Router.
# - Không chấm điểm trắc nghiệm.
# - Không lưu câu hỏi vào Database.
#
# Lưu ý về ownership:
# Request thiết kế hiện tại chỉ chứa child_id, không có user_id.
# Vì vậy không thể kiểm tra hồ sơ thuộc user_id nào
# nếu không bổ sung thông tin vào contract.
# Với bản demo hiện tại, chỉ kiểm tra child_id tồn tại.


# 5. KIỂM TRA API
#
# TODO:
# - Sinh bài trắc nghiệm một đáp án.
# - Sinh bài trắc nghiệm nhiều đáp án.
# - Sinh bài với 1 câu.
# - Sinh bài với 5 câu.
# - Gửi child_id không tồn tại.
# - Mô phỏng LLM trả dữ liệu lỗi.



"""API Module 1: Sinh bài trắc nghiệm cho trẻ."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from postgrest.exceptions import APIError
from supabase import AsyncClient

from app.config import get_settings
from app.database import get_supabase

from app.egm.module1_egm import (
    InvalidModelOutputError,
    generate_quiz,
)

from app.llm_client import (
    LLMClientError,
    LLMTimeoutError,
    LLMUnavailableError,
    call_llm,
)

logger = logging.getLogger(__name__)


from app.schemas.module1 import (
    QuizGenerateRequest,
    QuizGenerateResponse,
)


# ============================================================
# 1. KHỞI TẠO ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/exercises/quiz",
    tags=["Module 1 - Trắc nghiệm"]
)

logger = logging.getLogger(__name__)


# ============================================================
# 2. HÀM TRẢ RESPONSE LỖI
# ============================================================

def error_response(
    status_code: int,
    message: str,
    code: str
) -> JSONResponse:
    """
    Chuẩn hóa cấu trúc response lỗi.

    Ví dụ:
        error_response(
            404,
            "Không tìm thấy hồ sơ trẻ",
            "CHILD_NOT_FOUND"
        )
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
# 3. API SINH BÀI TẬP TRẮC NGHIỆM
# ============================================================

@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    status_code=200
)
async def generate_quiz_endpoint(
    request: QuizGenerateRequest,
    db: AsyncClient = Depends(get_supabase)
):
    """
    Endpoint:
        POST /api/exercises/quiz/generate

    Input:
        QuizGenerateRequest

    Output:
        QuizGenerateResponse

    Quy trình:
        1. FastAPI/Pydantic kiểm tra request.
        2. Tìm hồ sơ trẻ bằng child_id.
        3. Lấy age từ Database.
        4. Gọi EGM sinh câu hỏi qua LLM Server.
        5. Trả bộ câu hỏi đã validate cho Frontend.

    Chú ý:
        Contract MVP hiện chưa truyền user_id,
        nên chỉ có thể kiểm tra child_id tồn tại.
    """

    # --------------------------------------------------------
    # BƯỚC 1: TÌM HỒ SƠ TRẺ TRONG DATABASE
    # --------------------------------------------------------

    try:
        result = await (
            db.table("child_profiles")
            .select("id, age, gender, interests")
            .eq("id", request.child_id)
            .limit(1)
            .execute()
        )

    except APIError:

        logger.exception(
            "Không đọc được child_profiles"
        )

        return error_response(
            503,
            "Không thể truy cập cơ sở dữ liệu",
            "DATABASE_ERROR"
        )

    # --------------------------------------------------------
    # BƯỚC 2: KIỂM TRA CHILD_ID
    # --------------------------------------------------------

    # Nếu không có hồ sơ trong Database:
    if not result.data:

        return error_response(
            404,
            "Không tìm thấy hồ sơ trẻ",
            "CHILD_NOT_FOUND"
        )

    # ========================================================
    # BƯỚC 2.1: LẤY THÔNG TIN HỒ SƠ TRẺ
    # ========================================================

    # Lấy hồ sơ trẻ từ kết quả truy vấn Supabase.
    profile = result.data[0]

    # Lấy tuổi từ hồ sơ.
    age = profile.get("age")

    # Kiểm tra dữ liệu tuổi.
    if (
        not isinstance(age, int)
        or not 3 <= age <= 15
    ):

        return error_response(
            422,
            "Tuổi trong hồ sơ không hợp lệ",
            "INVALID_CHILD_AGE"
        )

    # ========================================================
    # BƯỚC 2.2: LẤY GIỚI TÍNH CỦA TRẺ
    # ========================================================

    # Lấy gender từ Database.
    # Ví dụ: "Nam", "Nữ" hoặc None.
    raw_gender = profile.get("gender")

    # Loại bỏ khoảng trắng thừa.
    # Nếu gender không phải chuỗi hoặc rỗng,
    # sử dụng None.
    gender = (
        (raw_gender.strip() or None)
        if isinstance(raw_gender, str)
        else None
    )

    # ========================================================
    # BƯỚC 2.3: LẤY DANH SÁCH SỞ THÍCH CỦA TRẺ
    # ========================================================

    # Lấy interests từ Database.
    # Ví dụ: ["Động vật", "Vẽ tranh"].
    raw_interests = profile.get("interests")

    # Kiểm tra interests có phải danh sách không.
    if isinstance(raw_interests, list):

        # Loại bỏ phần tử không phải chuỗi,
        # chuỗi rỗng và khoảng trắng thừa.
        interests = [
            item.strip()
            for item in raw_interests
            if isinstance(item, str) and item.strip()
        ]

    else:
        # Không có sở thích thì dùng danh sách rỗng.
        interests = []

    # --------------------------------------------------------
    # BƯỚC 3: GỌI EGM SINH CÂU HỎI
    # --------------------------------------------------------
    try:

        quiz_data = await generate_quiz(
            request=request,
            age=age,
            gender=gender,
            interests=interests,

            # Hàm gửi HTTP request đến LLM Server.
            llm_generate=call_llm_for_quiz,

            # Model lấy từ file .env thông qua Settings.
            model_name=get_settings().LLM_GENERATION_MODEL,

            # Thử lại tối đa 2 lần nếu output sai schema.
            max_attempts=2
        )
    # --------------------------------------------------------
    # BƯỚC 4: XỬ LÝ LỖI LLM
    # --------------------------------------------------------

    except LLMTimeoutError:

        return error_response(
            504,
            "LLM Server phản hồi quá chậm",
            "LLM_TIMEOUT"
        )

    except LLMUnavailableError:

        return error_response(
            503,
            "LLM Server đang không khả dụng",
            "LLM_UNAVAILABLE"
        )

    except (
        LLMClientError,
        InvalidModelOutputError
    ):

        return error_response(
            502,
            "Không tạo được bộ câu hỏi hợp lệ",
            "INVALID_MODEL_OUTPUT"
        )

    # --------------------------------------------------------
    # BƯỚC 5: TRẢ RESPONSE CHO FRONTEND
    # --------------------------------------------------------

    return QuizGenerateResponse(
        success=True,
        message="Tạo bài tập thành công",
        data=quiz_data
    )


async def call_llm_for_quiz(payload: dict) -> dict:
    """
    Chuyển đổi giao diện giữa Module 1 và llm_client.

    Module 1 EGM:
        Input: dict payload
        Output: dict response

    llm_client hiện tại:
        Input: task, prompt, model, ...
        Output: str content
    """

    # Tách dict thành các keyword arguments cho call_llm.
    content = await call_llm(**payload)

    # Đóng gói chuỗi content về dạng EGM Module 1 mong đợi.
    return {
        "success": True,
        "data": {
            "content": content
        }
    }
# ============================================================
# FILE: app/routers/module2.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Cung cấp hai API:
# - Sinh câu hỏi mở.
# - Đánh giá câu trả lời của trẻ.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - fastapi.APIRouter
# - fastapi.HTTPException
# - app.database.get_supabase
# - app.schemas.module2:
#     OpenGenerateRequest, OpenGenerateResponse,
#     OpenEvaluateRequest, OpenEvaluateResponse
# - app.egm.module2_egm:
#     generate_open_questions, evaluate_open_answer
#
# Khởi tạo router với prefix="/api/exercises/open".

import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

#from app.database import get_supabase
from app.egm.module2_egm import LLMOutputError
from app.egm.module2_egm import evaluate_open_answer as egm_evaluate_open_answer
from app.egm.module2_egm import generate_open_questions as egm_generate_open_questions
from app.llm_client import LLMClientError, LLMTimeoutError, LLMUnavailableError
from app.schemas.module2 import (
    OpenEvaluateRequest,
    OpenEvaluateResponse,
    OpenGenerateRequest,
    OpenGenerateResponse,
)

logger = logging.getLogger(__name__) 
router = APIRouter(prefix ="/api/exercises/open" , tags=["Module 2 - Bài tập mở"])
CHILD_TABLE = "ChildProfile"
CHILD_ID_COLUMN = "child_id"

#Hàm phụ 
def _error(status_code: int, code: str, message: str) -> HTTPException:
    """Tạo lỗi theo định dạng chung của nhóm:
    {"success": false, "message": "...", "error": {"code": "..."}}
    Nằm trong khóa "detail" vì FastAPI luôn bọc HTTPException như vậy."""
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message, "error": {"code": code}},
    )


def _llm_http_error(e: LLMClientError) -> HTTPException:
    """Đổi lỗi LLM thành HTTP phù hợp. Chỉ trả câu tiếng Việt cố định, KHÔNG trả str(e)
    vì nội dung lỗi có thể chứa nguyên văn dữ liệu model sinh ra.
    Thứ tự kiểm tra: lớp con trước, lớp cha (LLMClientError) sau cùng."""
    if isinstance(e, LLMTimeoutError):
        return _error(504, "LLM_TIMEOUT", "Hệ thống xử lý quá lâu, em thử lại sau nhé.")
    if isinstance(e, LLMUnavailableError):
        return _error(503, "LLM_UNAVAILABLE", "Hệ thống AI tạm thời chưa sẵn sàng, em thử lại sau nhé.")
    if isinstance(e, LLMOutputError):
        return _error(502, "LLM_INVALID_OUTPUT", "Hệ thống chưa tạo được kết quả hợp lệ, em thử lại nhé.")
    return _error(502, "LLM_ERROR", "Hệ thống AI gặp sự cố, em thử lại sau nhé.")


def _query_child_row(child_id: int):
    """Truy vấn hồ sơ trẻ trong Supabase. Hàm này là đồng bộ (blocking)."""
    result = (
        get_supabase()
        .table(CHILD_TABLE)
        .select("age")
        .eq(CHILD_ID_COLUMN, child_id)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


async def _get_child_age(child_id: int) -> int:
    """Bước 'truy vấn hồ sơ trẻ, lấy tuổi' dùng chung cho cả 2 API.
    run_in_threadpool: chạy lệnh DB blocking ở luồng phụ để server không bị đứng."""
    try:
        row = await run_in_threadpool(_query_child_row, child_id)
    except Exception as e:  # lỗi DB/mạng: không để lộ chi tiết ra FE
        logger.error("Module 2: lỗi đọc hồ sơ trẻ: %s", type(e).__name__)
        raise _error(503, "DATABASE_ERROR", "Chưa đọc được hồ sơ của bé, vui lòng thử lại sau.") from e

    if row is None:
        raise _error(404, "CHILD_NOT_FOUND", "Không tìm thấy hồ sơ của bé.")

    age = row.get("age")
    if not isinstance(age, int):
        raise _error(422, "CHILD_AGE_MISSING", "Hồ sơ của bé chưa có tuổi, hãy cập nhật hồ sơ.")
    return age

def _query_child_row(child_id: int):
    """Truy vấn hồ sơ trẻ trong Supabase. Hàm này là đồng bộ (blocking)."""
    from app.database import get_supabase   # import muộn: chỉ cần khi thật sự đọc DB

    result = (
        get_supabase()
        .table(CHILD_TABLE)
        .select("age")
        .eq(CHILD_ID_COLUMN, child_id)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None

# 2. HÀM generate_open_questions()
#
# Endpoint:
# POST /api/exercises/open/generate
#
# Input:
# - OpenGenerateRequest
#
# Output:
# - OpenGenerateResponse
#
# TODO:
# Bước 1:
#     Nhận cấu hình bài tập.
#
# Bước 2:
#     Kiểm tra request.
#
# Bước 3:
#     Truy vấn hồ sơ trẻ theo child_id.
#
# Bước 4:
#     Lấy độ tuổi của trẻ.
#
# Bước 5:
#     Gọi EGM sinh câu hỏi mở.
#
# Bước 6:
#     Nhận danh sách câu hỏi đã được kiểm tra.
#
# Bước 7:
#     Trả response cho FE.


@router.post("/generate" , response_model = OpenGenerateResponse)
async def generate_open_questions(request:OpenGenerateRequest) -> OpenGenerateResponse:
    # Bước 1, 2: nhận cấu hình và kiểm tra request -> FastAPI + Pydantic đã tự làm
    # (sai môn học, level, question_type, question_count ngoài 1-5... đều trả HTTP 422)

    # Bước 3, 4: truy vấn hồ sơ trẻ, lấy tuổi
    age = await _get_child_age(request.child_id)

    # Bước 5, 6: gọi EGM sinh câu hỏi, nhận danh sách đã được kiểm tra
    try:
        exercise = await egm_generate_open_questions(request, age)
    except LLMClientError as e:
        logger.warning("Module 2 generate: lỗi LLM: %s", type(e).__name__)
        raise _llm_http_error(e) from e

    # Bước 7: trả response cho FE
    return OpenGenerateResponse(data=exercise)


# 3. HÀM evaluate_open_answer()
#
# Endpoint:
# POST /api/exercises/open/evaluate
#
# Input:
# - OpenEvaluateRequest
#
# Output:
# - OpenEvaluateResponse
#
# TODO:
# Bước 1:
#     Nhận câu hỏi, câu trả lời và tiêu chí đánh giá.
#
# Bước 2:
#     Kiểm tra dữ liệu đầu vào.
#
# Bước 3:
#     Nếu câu trả lời rỗng, trả HTTP 422.
#
# Bước 4:
#     Kiểm tra child_id tồn tại và lấy độ tuổi.
#
# Bước 5:
#     Gọi evaluate_open_answer() trong EGM.
#
# Bước 6:
#     Nhận kết quả đánh giá đã chuẩn hóa.
#
# Bước 7:
#     Trả điểm và nhận xét cho FE.

@router.post("/evaluate", response_model=OpenEvaluateResponse)
async def evaluate_open_answer(request: OpenEvaluateRequest) -> OpenEvaluateResponse:
    # Bước 1, 2, 3: kiểm tra đầu vào. Câu trả lời rỗng (kể cả chỉ có dấu cách)
    # đã bị schema chặn và FastAPI tự trả HTTP 422, không cần viết thêm ở đây.

    # Bước 4: kiểm tra child_id tồn tại và lấy tuổi
    age = await _get_child_age(request.child_id)

    # Bước 5, 6: gọi EGM đánh giá, nhận kết quả đã chuẩn hóa
    try:
        result = await egm_evaluate_open_answer(request, age)
    except LLMClientError as e:
        # Chỉ ghi tên lỗi, KHÔNG ghi câu trả lời của trẻ hay nội dung model trả về
        logger.warning("Module 2 evaluate: lỗi LLM: %s", type(e).__name__)
        raise _llm_http_error(e) from e

    # Bước 7: trả điểm và nhận xét cho FE
    return OpenEvaluateResponse(data=result)

# 4. XỬ LÝ LỖI
#
# TODO:
# - Hồ sơ trẻ không tồn tại.
# - Câu trả lời rỗng.
# - LLM Server không phản hồi.
# - Model trả dữ liệu không đúng cấu trúc.
# - Model trả điểm nằm ngoài thang 0 đến 10.
#
# Trả thông báo phù hợp, bằng tiếng Việt.


# 5. QUY ƯỚC
#
# - Không trực tiếp viết prompt trong Router.
# - Không xử lý kết quả model bằng cách đoán cấu trúc.
# - Không lưu lịch sử bài làm vào Database.
# - Đánh giá từng câu, không bắt buộc chấm toàn bộ bài.
# - Điểm LLM là đánh giá tham khảo.
#
# Tương tự Module 1, request hiện tại chỉ chứa child_id;
# việc kiểm tra sở hữu hồ sơ yêu cầu thống nhất thêm contract.


# 6. KIỂM TRA API
#
# TODO:
# - Sinh câu hỏi mở thành công.
# - Sinh đủ số lượng câu hỏi yêu cầu.
# - Đánh giá câu trả lời hợp lệ.
# - Đánh giá câu trả lời diễn đạt khác đáp án mẫu.
# - Đánh giá câu trả lời trống.
# - Mô phỏng lỗi LLM.
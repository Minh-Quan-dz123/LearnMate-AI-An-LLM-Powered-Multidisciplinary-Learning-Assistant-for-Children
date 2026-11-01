
"""
FILE: app/routers/llm.py

MỤC ĐÍCH:
    1. Tạo API endpoint cho Backend gọi LLM_V1.
    2. Tiếp nhận và kiểm tra request bằng Pydantic.
    3. Gọi Gemini Provider để sinh nội dung.
    4. Chuẩn hóa response trước khi trả về Backend.
    5. Xử lý lỗi khi Gemini không hoạt động.

API:
    POST /internal/llm/generate

LUỒNG XỬ LÝ:
    Backend
       -> FastAPI Router
       -> LLMGenerateRequest
       -> Gemini Provider
       -> LLMGenerateResponse
       -> Backend

LƯU Ý:
    Router không xây dựng prompt nghiệp vụ.
    Prompt được tạo bởi EGM trong BE.
"""


# ==================================================
# 1. IMPORT THƯ VIỆN
# ==================================================

# APIRouter:
#     Class do FastAPI cung cấp để tạo nhóm API.
#
# HTTPException:
#     Ngoại lệ dùng để trả HTTP error cho client.
#
# status:
#     Chứa hằng số mã HTTP, ví dụ:
#       status.HTTP_502_BAD_GATEWAY = 502
#       status.HTTP_503_SERVICE_UNAVAILABLE = 503
from fastapi import APIRouter, HTTPException, status


# Import các Pydantic model đã viết ở bước 7.
#
# LLMGenerateRequest:
#     Kiểm tra JSON do Backend gửi tới.
#
# LLMGenerateData:
#     Chứa nội dung JSON do Gemini sinh ra.
#
# LLMGenerateResponse:
#     Định nghĩa response trả lại Backend.
from app.schemas import (
    LLMGenerateRequest,
    LLMGenerateData,
    LLMGenerateResponse
)


# Import hàm generate() từ Gemini Provider.
#
# "as generate_gemini":
#     Đặt tên khác cho hàm được import.
#
# Ví dụ:
#     generate_gemini(prompt="...")
#
# Giúp phân biệt hàm của Provider với hàm của Router.
from app.providers.gemini import (
    generate as generate_gemini,
    GeminiProviderError,
    GeminiOutputError
)


# ==================================================
# 2. KHỞI TẠO ROUTER
# ==================================================

# APIRouter() tạo một đối tượng quản lý các API.
#
# tags=["LLM"]:
#     Nhóm các endpoint dưới nhãn "LLM"
#     trong giao diện Swagger UI.
#
# Ví dụ:
#     Swagger hiển thị nhóm LLM:
#       POST /internal/llm/generate
router = APIRouter(
    tags=["LLM"]
)


# ==================================================
# 3. API SINH NỘI DUNG BẰNG LLM
# ==================================================

# @router.post():
#     Decorator đăng ký một HTTP POST endpoint.
#
# "/internal/llm/generate":
#     Đường dẫn endpoint.
#
# response_model:
#     Yêu cầu FastAPI kiểm tra và tuần tự hóa
#     kết quả theo LLMGenerateResponse.
#
# status_code=200:
#     Mã HTTP thành công.
#
# Hàm bên dưới được thực thi khi request POST
# đến endpoint này.
@router.post(
    "/internal/llm/generate",
    response_model=LLMGenerateResponse,
    status_code=status.HTTP_200_OK
)
async def generate_content(
    request: LLMGenerateRequest
) -> LLMGenerateResponse:
    """
    Nhận yêu cầu từ BE và gọi Gemini.

    THAM SỐ:
        request:
            Đối tượng LLMGenerateRequest do FastAPI
            tạo từ JSON trong HTTP request.

    VÍ DỤ:
        {
            "task": "Sinh câu hỏi trắc nghiệm",
            "model": "default",
            "prompt": "Tạo 2 câu hỏi về động vật...",
            "temperature": 0.5,
            "max_output_tokens": 1800
        }

    ĐẦU RA:
        LLMGenerateResponse:
            {
                "success": true,
                "message": "Mô hình đã tạo nội dung",
                "data": {
                    "content": "Chuỗi JSON Gemini trả về"
                }
            }

    LƯU Ý:
        Hàm sử dụng async vì gọi Gemini thông qua
        hàm generate() bất đồng bộ.
    """

    # ------------------------------------------------
    # BƯỚC 1: NHẬN VÀ KIỂM TRA REQUEST
    # ------------------------------------------------

    # FastAPI tự động:
    #   1. Đọc JSON từ request body.
    #   2. Tạo LLMGenerateRequest.
    #   3. Kiểm tra kiểu và ràng buộc Pydantic.
    #
    # Nếu JSON sai:
    #   FastAPI trả HTTP 422 tự động.
    #
    # Ví dụ:
    #   prompt="" -> HTTP 422
    #
    # Đến được đây nghĩa là request đã vượt qua
    # các bước kiểm tra Pydantic.

    # task:
    #   Tên tác vụ do BE gửi, ví dụ Module 1
    #   hoặc Module 2.
    #
    # Trong phiên bản này, Provider dùng chung
    # một model, nên không cần phân nhánh theo task.
    #
    # request.model hiện là nhãn logic.
    # Gemini Provider sử dụng GEMINI_MODEL từ .env,
    # chưa hỗ trợ chọn model động theo request.

    # ------------------------------------------------
    # BƯỚC 2: GỌI GEMINI PROVIDER
    # ------------------------------------------------

    try:
        # generate_gemini() được import từ:
        # app/providers/gemini.py
        #
        # request.prompt:
        #     Prompt nghiệp vụ do BE xây dựng.
        #
        # request.temperature:
        #     Mức ngẫu nhiên khi sinh nội dung.
        #
        # request.max_output_tokens:
        #     Giới hạn token đầu ra.
        #
        # await:
        #     Chờ hàm bất đồng bộ hoàn thành.
        #
        # content:
        #     Chuỗi JSON hợp lệ do Gemini trả về.
        content = await generate_gemini(
            prompt=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens
        )

    # ------------------------------------------------
    # BƯỚC 3: XỬ LÝ LỖI OUTPUT
    # ------------------------------------------------

    except GeminiOutputError as exc:
        # GeminiOutputError xảy ra khi:
        #   - Gemini trả về nội dung rỗng.
        #   - Gemini trả JSON sai cú pháp.
        #   - Kết quả không phải JSON object.
        #
        # HTTP 502:
        #   LLM_V1 nhận kết quả không hợp lệ
        #   từ nhà cung cấp model.
        #
        # Không trả raw output cho phía Backend.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini trả về dữ liệu không hợp lệ"
        ) from exc

    # ------------------------------------------------
    # BƯỚC 4: XỬ LÝ LỖI PROVIDER
    # ------------------------------------------------

    except GeminiProviderError as exc:
        # GeminiProviderError xảy ra khi SDK báo lỗi,
        # ví dụ:
        #   - API key không có quyền truy cập.
        #   - Vượt quá giới hạn quota.
        #   - Model tạm thời không khả dụng.
        #
        # Phiên bản đơn giản này gom các lỗi API
        # thành HTTP 503.
        #
        # Sau này có thể phân loại chi tiết hơn:
        #   429 -> rate limit
        #   504 -> timeout
        #   502 -> provider trả lỗi khác.
        #
        # Không trả API key hoặc lỗi nội bộ
        # của SDK ra HTTP response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối hoặc sử dụng Gemini"
        ) from exc

    # ------------------------------------------------
    # BƯỚC 5: TẠO RESPONSE THÀNH CÔNG
    # ------------------------------------------------

    # LLMGenerateData:
    #     Pydantic model chứa trường content.
    #
    # content vẫn là chuỗi JSON.
    #
    # Ví dụ:
    #     content = '{"questions":[]}'
    data = LLMGenerateData(
        content=content
    )

    # LLMGenerateResponse:
    #     Pydantic model định nghĩa response cuối.
    #
    # success và message đã có giá trị mặc định
    # được khai báo trong app/schemas.py.
    response = LLMGenerateResponse(
        data=data
    )

    # ------------------------------------------------
    # BƯỚC 6: TRẢ RESPONSE VỀ BACKEND
    # ------------------------------------------------

    # return trả đối tượng Pydantic về FastAPI.
    #
    # FastAPI tự chuyển kết quả sang JSON để
    # gửi qua HTTP.
    #
    # Khi đó Backend nhận:
    # {
    #     "success": true,
    #     "message": "Mô hình đã tạo nội dung",
    #     "data": {
    #         "content": "{\"questions\":[]}"
    #     }
    # }
    return response

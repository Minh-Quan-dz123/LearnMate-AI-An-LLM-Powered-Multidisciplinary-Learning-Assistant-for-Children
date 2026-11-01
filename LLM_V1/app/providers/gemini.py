
"""
FILE: app/providers/gemini.py

MỤC ĐÍCH:
    1. Kết nối đến Gemini API bằng SDK google-genai.
    2. Nhận prompt do Backend xây dựng.
    3. Gửi prompt đến model Gemini.
    4. Yêu cầu Gemini trả về JSON.
    5. Kiểm tra JSON hợp lệ trước khi trả kết quả.
    6. Xử lý các lỗi cơ bản khi gọi API.

VAI TRÒ:
    Đây là Provider Adapter, không chứa logic nghiệp vụ.

    File này KHÔNG:
        - Tự xây prompt trắc nghiệm.
        - Tự xây prompt đánh giá.
        - Chấm điểm câu trả lời.
        - Giao tiếp trực tiếp với Frontend.

ĐẦU VÀO:
    prompt: str
    temperature: float
    max_output_tokens: int

ĐẦU RA:
    str - Chuỗi JSON mà Gemini tạo ra.
"""

# ==================================================
# 1. IMPORT CÁC THƯ VIỆN
# ==================================================

# json là thư viện chuẩn của Python.
#
# json.loads():
#     Chuyển chuỗi JSON thành đối tượng Python.
#
# Ví dụ:
#     json.loads('{"score": 10}')
#     -> {"score": 10} (dict)
import json

# genai thuộc thư viện google-genai.
#
# genai.Client():
#     Khởi tạo client kết nối Gemini.
#
# types:
#     Chứa các class cấu hình request.
#
# errors:
#     Chứa các lớp ngoại lệ của Gemini SDK.
from google import genai
from google.genai import types, errors

# Import hàm đọc cấu hình đã viết ở bước 5.
#
# app.config:
#     Module config.py nằm trong package app.
#
# get_settings:
#     Hàm trả về đối tượng Settings.
from app.config import get_settings


# ==================================================
# 2. ĐỊNH NGHĨA CÁC LOẠI LỖI
# ==================================================

class GeminiProviderError(Exception):
    """
    Lỗi chung khi làm việc với Gemini Provider.

    Exception:
        Lớp ngoại lệ cơ bản của Python.

    Kế thừa Exception giúp chương trình có thể:
        raise GeminiProviderError("Thông báo lỗi")

    Và các module khác có thể:
        except GeminiProviderError:
            ...
    """


class GeminiOutputError(GeminiProviderError):
    """
    Lỗi khi kết quả Gemini trả về không hợp lệ.

    Kế thừa GeminiProviderError nên có thể được
    bắt bằng cả GeminiOutputError và lớp cha.

    Ví dụ:
        Gemini trả:
            "Xin chào!"

        Trong khi hệ thống yêu cầu JSON.

        -> Phát sinh GeminiOutputError.
    """


# ==================================================
# 3. HÀM GỌI GEMINI API
# ==================================================

async def generate(
    prompt: str,
    temperature: float = 0.5,
    max_output_tokens: int = 1800
) -> str:
    """
    Gửi prompt đến Gemini API và trả về chuỗi JSON.

    THAM SỐ:
        prompt:
            Nội dung yêu cầu gửi đến Gemini.

        temperature:
            Điều khiển mức ngẫu nhiên khi sinh nội dung.
            Ở đây mặc định = 0.5 để khớp contract BE.
            Model khác nhau có thể có khuyến nghị khác.

        max_output_tokens:
            Giới hạn token đầu ra của model.
            Mặc định = 1800.

    KIỂU TRẢ VỀ:
        str:
            Chuỗi JSON hợp lệ do Gemini tạo.

    VÍ DỤ:
        result = await generate(
            prompt="Trả JSON mô tả con mèo",
            temperature=0.5,
            max_output_tokens=1000
        )

    LƯU Ý:
        Đây là hàm bất đồng bộ (async).
        Phải sử dụng await khi gọi trong hàm async.
    """

    # ------------------------------------------------
    # BƯỚC 1: KIỂM TRA ĐẦU VÀO
    # ------------------------------------------------

    # isinstance(obj, type):
    #     Kiểm tra đối tượng có thuộc kiểu type không.
    #
    # prompt.strip():
    #     Loại bỏ khoảng trắng đầu và cuối chuỗi.
    #
    # Ví dụ:
    #     "   ".strip() -> ""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(
            "Prompt phải là chuỗi không rỗng"
        )

    # max_output_tokens phải là số nguyên dương.
    if (
        not isinstance(max_output_tokens, int)
        or max_output_tokens <= 0
    ):
        raise ValueError(
            "max_output_tokens phải là số nguyên dương"
        )

    # ------------------------------------------------
    # BƯỚC 2: ĐỌC CẤU HÌNH
    # ------------------------------------------------

    # get_settings() được import từ app/config.py.
    #
    # Kết quả là đối tượng Settings có các thuộc tính:
    #     gemini_api_key
    #     gemini_model
    #     llm_provider
    #     llm_host
    #     llm_port
    settings = get_settings()

    # Không hardcode API key hoặc tên model trong file.
    api_key = settings.gemini_api_key
    model_name = settings.gemini_model

    # ------------------------------------------------
    # BƯỚC 3: TẠO CẤU HÌNH SINH NỘI DUNG
    # ------------------------------------------------

    # types.GenerateContentConfig là class do SDK cung cấp.
    #
    # temperature:
    #     Tham số điều khiển tính ngẫu nhiên.
    #
    # max_output_tokens:
    #     Giới hạn số token model được sử dụng
    #     để tạo kết quả.
    #
    # response_mime_type="application/json":
    #     Yêu cầu model trả kết quả dạng JSON.
    #
    # Chưa khai báo response_schema vì mỗi tác vụ
    # của Backend có cấu trúc JSON khác nhau.
    #
    # JSON mode KHÔNG thay thế kiểm tra schema
    # nghiệp vụ của Backend.
    generation_config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json"
    )

    # ------------------------------------------------
    # BƯỚC 4: GỌI GEMINI API
    # ------------------------------------------------

    try:
        # Tạo Client bằng API key.
        #
        # .aio:
        #     Giao diện bất đồng bộ của SDK.
        #
        # async with ... as client:
        #     Mở và quản lý async client.
        #     Tự đóng client khi kết thúc khối lệnh.
        #
        # Ví dụ:
        #     Gemini nhận request trong lúc FastAPI
        #     có thể xử lý công việc bất đồng bộ khác.
        async with genai.Client(api_key=api_key).aio as client:

            # await:
            #     Chờ một thao tác bất đồng bộ hoàn thành.
            #
            # client.models.generate_content():
            #     Gửi yêu cầu tạo nội dung đến Gemini.
            #
            # model:
            #     Mã model đọc từ .env.
            #
            # contents:
            #     Prompt cần gửi.
            #
            # config:
            #     Các thông số tạo nội dung.
            response = await client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=generation_config
            )

    except errors.APIError as exc:
        # APIError là lỗi do Gemini SDK báo về.
        #
        # exc.code chứa mã lỗi HTTP, ví dụ:
        #     400: Request không hợp lệ.
        #     403: Không được phép truy cập.
        #     404: Model không tồn tại/không khả dụng.
        #     429: Quá giới hạn request/token.
        #     503: Dịch vụ tạm thời không khả dụng.
        #
        # Không in API key hay thông tin nhạy cảm.
        #
        # "from exc" giữ lại ngoại lệ gốc để debug.
        raise GeminiProviderError(
            f"Gọi Gemini API thất bại (HTTP {exc.code})"
        ) from exc

    # ------------------------------------------------
    # BƯỚC 5: LẤY VĂN BẢN TỪ RESPONSE
    # ------------------------------------------------

    # response.text là thuộc tính tiện ích của SDK
    # chứa văn bản Gemini sinh ra.
    #
    # Ví dụ:
    #     '{"questions": [...]}'
    content = response.text

    # Nếu không có văn bản trả về:
    if not content or not content.strip():
        raise GeminiOutputError(
            "Gemini không trả về nội dung"
        )

    # ------------------------------------------------
    # BƯỚC 6: KIỂM TRA JSON HỢP LỆ
    # ------------------------------------------------

    try:
        # json.loads(content):
        #     Chuyển chuỗi JSON thành dữ liệu Python.
        #
        # Ví dụ:
        #     content = '{"score": 8.5}'
        #
        #     parsed = json.loads(content)
        #
        # Kết quả:
        #     parsed = {"score": 8.5}
        parsed = json.loads(content)

    except json.JSONDecodeError as exc:
        # Trường hợp Gemini trả chuỗi JSON lỗi.
        #
        # Ví dụ:
        #     '{"score": 8.5'
        #
        # Thiếu dấu } nên không parse được.
        raise GeminiOutputError(
            "Gemini trả về JSON không hợp lệ"
        ) from exc

    # Hệ thống yêu cầu JSON ở cấp cao nhất là object.
    #
    # Trong Python, JSON object được biểu diễn
    # bằng kiểu dict.
    #
    # Ví dụ hợp lệ:
    #     {"questions": [...]}
    #
    # Ví dụ không hợp lệ theo contract hiện tại:
    #     ["câu 1", "câu 2"]
    if not isinstance(parsed, dict):
        raise GeminiOutputError(
            "Kết quả Gemini phải là JSON object"
        )

    # ------------------------------------------------
    # BƯỚC 7: TRẢ KẾT QUẢ
    # ------------------------------------------------

    # Trả về CHUỖI JSON ban đầu.
    #
    # Không trả về parsed vì Backend hiện tại
    # cần nhận một chuỗi để EGM xử lý.
    #
    # Ví dụ:
    #     '{"questions": [...]}'
    #
    # Sau này FastAPI Router sẽ đặt chuỗi này
    # vào response["data"]["content"].
    return content

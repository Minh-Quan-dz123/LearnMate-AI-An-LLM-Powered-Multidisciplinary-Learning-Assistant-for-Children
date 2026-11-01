
"""
FILE: app/schemas.py

MỤC ĐÍCH:
    Định nghĩa và kiểm tra cấu trúc dữ liệu
    giao tiếp giữa BE và LLM_V1.

Bao gồm:
    1. LLMGenerateRequest:
        Kiểm tra request do Backend gửi tới.

    2. LLMGenerateData:
        Chứa nội dung JSON do Gemini sinh ra.

    3. LLMGenerateResponse:
        Định nghĩa response trả lại Backend.

LƯU Ý:
    File này chỉ định nghĩa cấu trúc dữ liệu.
    Không gọi Gemini API và không xử lý nghiệp vụ.
"""

# ==================================================
# 1. IMPORT THƯ VIỆN
# ==================================================

# Literal cho phép quy định một giá trị cố định.
#
# Ví dụ:
#   Literal[True] -> chỉ chấp nhận giá trị True.
from typing import Literal

# BaseModel:
#   Lớp cơ sở để định nghĩa Pydantic model.
#
# Field:
#   Khai báo giá trị mặc định và ràng buộc dữ liệu.
#
# field_validator:
#   Decorator dùng để kiểm tra/xử lý giá trị
#   của từng thuộc tính trong Pydantic model.
#
# ConfigDict:
#   Cấu hình hành vi của Pydantic model.
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator
)


# ==================================================
# 2. SCHEMA REQUEST: BE -> LLM_V1
# ==================================================

class LLMGenerateRequest(BaseModel):
    """
    Định nghĩa request gửi từ Backend.

    Ví dụ:
        {
            "task": "Sinh câu hỏi trắc nghiệm",
            "model": "default",
            "prompt": "Tạo 2 câu hỏi...",
            "temperature": 0.5,
            "max_output_tokens": 1800
        }
    """

    # ConfigDict(extra="forbid"):
    #   Không chấp nhận các trường JSON không được
    #   khai báo trong class này.
    #
    # Ví dụ request chứa "unknown_field" sẽ bị lỗi.
    model_config = ConfigDict(extra="forbid")

    # task: tên tác vụ do Backend gửi.
    #
    # str: yêu cầu dữ liệu kiểu chuỗi.
    #
    # Field(min_length=1):
    #   Chuỗi phải có ít nhất một ký tự.
    #
    # Không khai báo default -> trường bắt buộc.
    task: str = Field(min_length=1)

    # model là tên hoặc nhãn logic của model.
    #
    # "default" sẽ được LLM Server ánh xạ
    # tới GEMINI_MODEL trong .env.
    #
    # Việc ánh xạ thực hiện ở router/provider,
    # không thực hiện trong schema.
    model: str = Field(
        default="default",
        min_length=1
    )

    # prompt chứa yêu cầu nghiệp vụ do BE tạo.
    # Không tự tạo hoặc sửa nội dung prompt ở đây.
    prompt: str = Field(min_length=1)

    # temperature: tham số điều chỉnh độ ngẫu nhiên.
    #
    # float: số thực.
    #
    # ge = greater than or equal (>=)
    # le = less than or equal (<=)
    #
    # 0.0 <= temperature <= 2.0
    temperature: float = Field(
        default=0.5,
        ge=0.0,
        le=2.0
    )

    # max_output_tokens: giới hạn số token đầu ra.
    #
    # int: số nguyên.
    # gt=0: phải lớn hơn 0.
    #
    # Ví dụ:
    #   1800 -> hợp lệ
    #   -10  -> không hợp lệ
    max_output_tokens: int = Field(
        default=1800,
        gt=0
    )

    # ------------------------------------------------
    # KIỂM TRA CÁC TRƯỜNG VĂN BẢN
    # ------------------------------------------------

    # @field_validator:
    #   Đăng ký hàm kiểm tra các trường chỉ định.
    #
    # Một validator có thể dùng cho nhiều trường.
    #
    # Mặc định mode="after":
    #   Hàm chạy sau kiểm tra kiểu dữ liệu cơ bản.
    @field_validator("task", "model", "prompt")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """
        Loại bỏ khoảng trắng ở đầu và cuối chuỗi.

        cls:
            Đại diện class chứa phương thức.
            Python tự truyền vào khi gọi.

        value:
            Giá trị trường đang được kiểm tra.

        Ví dụ:
            "  Gemini  " -> "Gemini"

            "   " -> ValueError

        Trả về:
            Chuỗi đã được chuẩn hóa.
        """

        # Loại bỏ khoảng trắng ở hai đầu.
        value = value.strip()

        # Không chấp nhận chuỗi chỉ có khoảng trắng.
        if not value:
            raise ValueError(
                "Trường văn bản không được để trống"
            )

        return value


# ==================================================
# 3. SCHEMA DATA: NỘI DUNG DO LLM TRẢ VỀ
# ==================================================

class LLMGenerateData(BaseModel):
    """
    Định nghĩa trường data của response.

    Ví dụ:
        {
            "content": "{\"questions\":[]}"
        }

    content là chuỗi JSON, không phải dict.
    """

    # Gemini Provider trả về str.
    # Backend sẽ tiếp tục parse và validate
    # cấu trúc JSON nghiệp vụ ở EGM.
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def check_content(cls, value: str) -> str:
        """
        Kiểm tra chuỗi content không được rỗng.

        Không parse JSON ở đây vì gemini.py
        đã kiểm tra cú pháp JSON trước đó.
        """

        if not value.strip():
            raise ValueError(
                "content không được để trống"
            )

        return value


# ==================================================
# 4. SCHEMA RESPONSE: LLM_V1 -> BE
# ==================================================

class LLMGenerateResponse(BaseModel):
    """
    Định nghĩa response khi gọi model thành công.

    Ví dụ:
        {
            "success": true,
            "message": "Mô hình đã tạo nội dung",
            "data": {
                "content": "{\"questions\":[]}"
            }
        }
    """

    # Literal[True] quy định chỉ chấp nhận True.
    #
    # Schema này dành riêng cho response thành công.
    # Response lỗi sẽ được xử lý ở FastAPI Router.
    success: Literal[True] = True

    # Message mặc định trả về Backend.
    message: str = "Mô hình đã tạo nội dung"

    # data phải là đối tượng LLMGenerateData,
    # tức là chứa trường content có kiểu str.
    data: LLMGenerateData

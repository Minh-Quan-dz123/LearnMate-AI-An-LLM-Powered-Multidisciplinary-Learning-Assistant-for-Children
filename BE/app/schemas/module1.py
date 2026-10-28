# ============================================================
# FILE: app/schemas/module1.py
# PHỤ TRÁCH: QUÂN
#
# MỤC ĐÍCH:
# Định nghĩa cấu trúc Request và Response
# cho Module 1 - Bài tập trắc nghiệm.
#
# Hỗ trợ:
# - Trắc nghiệm một đáp án.
# - Trắc nghiệm nhiều đáp án.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel
# - pydantic.Field
# - pydantic.model_validator
# - app.constants:
#     Sử dụng các giá trị question_type, level và giới hạn số câu.


# 2. CLASS QuizGenerateRequest
#
# Dữ liệu FE gửi lên:
#
# - child_id: int
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - question_count: int
#
# TODO:
# - Kiểm tra child_id hợp lệ.
# - Kiểm tra subject và topic không rỗng.
# - Kiểm tra level là "Cơ bản" hoặc "Nâng cao".
# - Kiểm tra question_type là một trong hai loại trắc nghiệm.
# - Kiểm tra question_count trong khoảng 1 đến 5.
#
# Lưu ý:
# Tuổi được lấy từ Child Profile trong Database,
# không yêu cầu FE tự truyền tuổi.


# 3. CLASS QuizOption
#
# Đại diện cho một lựa chọn.
#
# Các trường:
# - option_id: str
# - text: str
#
# Ví dụ:
# {
#   "option_id": "A",
#   "text": "Con mèo"
# }


# 4. CLASS QuizQuestion
#
# Đại diện cho một câu hỏi trắc nghiệm.
#
# Các trường:
# - question_id: str
# - content: str
# - options: list[QuizOption]
# - correct_option_ids: list[str]
# - explanation: str
#
# TODO:
# - Kiểm tra nội dung câu hỏi không rỗng.
# - Kiểm tra danh sách options không rỗng.
# - Kiểm tra option_id không trùng nhau.
# - Kiểm tra correct_option_ids không trùng nhau.
# - Kiểm tra tất cả đáp án đúng tồn tại trong options.
# - Kiểm tra explanation không rỗng.
#
# Lưu ý:
# Điều kiện đúng 1 hoặc nhiều đáp án phụ thuộc question_type.
# Có thể thực hiện kiểm tra này trong EGM khi đã biết loại bài.


# 5. CLASS QuizData
#
# Dữ liệu bài tập trả về:
#
# - exercise_id: str
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - questions: list[QuizQuestion]
#
# TODO:
# - Đảm bảo mỗi question_id là duy nhất.
# - Đảm bảo số câu bằng question_count đã yêu cầu.
# - Đảm bảo các câu hỏi phù hợp question_type.


# 6. CLASS QuizGenerateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: QuizData
#
# Ví dụ cấu trúc:
# {
#   "success": true,
#   "message": "Tạo bài tập thành công",
#   "data": {
#     "exercise_id": "demo-bai-001",
#     "subject": "Khoa học tự nhiên",
#     "topic": "Động vật và thực vật",
#     "level": "Cơ bản",
#     "question_type": "Trắc nghiệm một đáp án",
#     "questions": []
#   }
# }
#
# questions ở ví dụ trên chỉ minh họa kiểu dữ liệu.
# Khi triển khai phải có số câu đúng theo request.


# 7. RÀNG BUỘC RIÊNG CHO QUESTION_TYPE
#
# Trắc nghiệm một đáp án:
# - Mỗi câu có đúng 1 correct_option_id.
#
# Trắc nghiệm nhiều đáp án:
# - Mỗi câu có tối thiểu 2 correct_option_ids.
#
# Các quy tắc về số phương án cần khớp prompt của EGM.


# 8. KIỂM TRA
#
# TODO:
# - question_count = 0.
# - question_count = 6.
# - Một đáp án nhưng model trả 2 đáp án đúng.
# - Đáp án đúng không tồn tại trong options.
# - Hai câu có question_id trùng nhau.
# - Model trả thiếu explanation.


from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# 1. CÁC GIÁ TRỊ ĐƯỢC PHÉP
QuizLevel = Literal["Cơ bản", "Nâng cao"]

QuizQuestionType = Literal[
    "Trắc nghiệm một đáp án",
    "Trắc nghiệm nhiều đáp án"
]


# 2. REQUEST SINH TRẮC NGHIỆM
class QuizGenerateRequest(BaseModel):

    child_id: int = Field(gt=0)

    subject: str = Field(min_length=1, max_length=100)

    topic: str = Field(min_length=1, max_length=200)

    level: QuizLevel

    question_type: QuizQuestionType

    question_count: int = Field(ge=1, le=5)

    @field_validator("subject", "topic")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Không được để trống môn học hoặc chủ đề")

        return value


# 3. MỘT PHƯƠNG ÁN TRẢ LỜI
class QuizOption(BaseModel):

    option_id: str = Field(min_length=1, max_length=20)

    text: str = Field(min_length=1)

    @field_validator("option_id", "text")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Phương án không được để trống")

        return value


# 4. MỘT CÂU HỎI TRẮC NGHIỆM
class QuizQuestion(BaseModel):

    question_id: str = Field(min_length=1)

    content: str = Field(min_length=1)

    options: list[QuizOption] = Field(min_length=3, max_length=5)

    correct_option_ids: list[str] = Field(min_length=1)

    explanation: str = Field(min_length=1)

    @field_validator("question_id", "content", "explanation")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Trường câu hỏi không được để trống")

        return value

    @model_validator(mode="after")
    def validate_answers(self):

        option_ids = [
            option.option_id
            for option in self.options
        ]

        # Không cho phép trùng ID phương án.
        if len(option_ids) != len(set(option_ids)):
            raise ValueError(
                "ID phương án không được trùng nhau"
            )

        # Không cho phép trùng ID đáp án đúng.
        if len(self.correct_option_ids) != len(
            set(self.correct_option_ids)
        ):
            raise ValueError(
                "Danh sách đáp án đúng có ID trùng nhau"
            )

        # Đáp án đúng phải thuộc danh sách phương án.
        if not set(self.correct_option_ids).issubset(
            set(option_ids)
        ):
            raise ValueError(
                "Đáp án đúng phải tồn tại trong các phương án"
            )

        return self


# 5. DỮ LIỆU BÀI TRẮC NGHIỆM
class QuizGenerateData(BaseModel):

    exercise_id: str = Field(min_length=1)

    subject: str = Field(min_length=1)

    topic: str = Field(min_length=1)

    level: QuizLevel

    question_type: QuizQuestionType

    questions: list[QuizQuestion] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_question_set(self):

        # Kiểm tra ID câu hỏi không trùng nhau.
        question_ids = [
            question.question_id
            for question in self.questions
        ]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "ID câu hỏi không được trùng nhau"
            )

        # Kiểm tra theo từng dạng trắc nghiệm.
        for question in self.questions:

            count = len(question.correct_option_ids)
            option_count = len(question.options)

            if self.question_type == "Trắc nghiệm một đáp án":

                if count != 1 or not 3 <= option_count <= 4:
                    raise ValueError(
                        "Câu một đáp án cần 3-4 lựa chọn "
                        "và đúng 1 đáp án"
                    )

            else:

                if not 2 <= count <= 3 or not 4 <= option_count <= 5:
                    raise ValueError(
                        "Câu nhiều đáp án cần 4-5 lựa chọn "
                        "và 2-3 đáp án đúng"
                    )

        return self


# 6. RESPONSE TRẢ VỀ FRONTEND
class QuizGenerateResponse(BaseModel):

    success: bool

    message: str

    data: QuizGenerateData

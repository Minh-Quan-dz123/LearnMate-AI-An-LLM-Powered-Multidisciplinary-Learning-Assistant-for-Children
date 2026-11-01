# ============================================================
# FILE: app/schemas/module2.py
# PHỤ TRÁCH: THANH
#
# MỤC ĐÍCH:
# Định nghĩa cấu trúc dữ liệu cho Module 2.
#
# Module 2 thực hiện:
# - Sinh câu hỏi mở.
# - Nhận câu trả lời của trẻ.
# - Trả kết quả đánh giá từ LLM.
# ============================================================


# 1. THƯ VIỆN CẦN IMPORT
#
# - pydantic.BaseModel
# - pydantic.Field
# - pydantic.model_validator nếu cần.
# - app.constants

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import (
    MAX_QUESTION_COUNT, MIN_QUESTION_COUNT, QUESTION_TYPES, SUBJECTS, SUPPORTED_LEVELS,
)

OPEN_QUESTION_TYPE = "Câu trả lời mở"
assert OPEN_QUESTION_TYPE in QUESTION_TYPES 
#lớp cha: tự cắt khoảng trắng đầu/cối ở mọi chuỗi
#Nhờ thế mà câu trả lười "    "(toàn dấu cách) bị coi là rỗng và bị chặn

class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

# 2. CLASS OpenGenerateRequest
#
# Các trường:
# - child_id: int
# - subject: str
# - topic: str
# - level: str
# - question_type: str
# - question_count: int
#
# TODO:
# - Kiểm tra child_id hợp lệ.
# - Kiểm tra dữ liệu môn học/chủ đề.
# - Kiểm tra level.
# - Chỉ chấp nhận question_type = "Câu trả lời mở".
# - Kiểm tra question_count từ 1 đến 5.

class OpenGenerateRequest(_Base):
    child_id: int = Field(... , gt = 0) #id hồ sơ của trẻ phải > 0
    subject: str = Field(... , min_length=1, max_length=100)
    topic: str = Field(... , min_length=1 , max_length=100) #topic hardcore hoặc user tự nhập
    level: str 
    question_type: str 
    question_count: int = Field(..., ge =MIN_QUESTION_COUNT , le =MAX_QUESTION_COUNT) 

    @field_validator("subject")
    @classmethod
    def check_subject(cls, v:str)-> str :
        if v not in SUBJECTS:
            raise ValueError(f"Môn học không hợp lệ. Chỉ nhận: {', '.join(SUBJECTS)} ")
        return v 

    @field_validator("level")
    @classmethod
    def check_level(cls, v:str)-> str :
        if v not in SUPPORTED_LEVELS:
            raise ValueError(f"Level không hợp lệ. Chỉ nhận: {', '.join(SUPPORTED_LEVELS)} ")
        return v 

    @field_validator("question_type")
    @classmethod
    def check_question_type(cls, v:str)-> str :
        if v != OPEN_QUESTION_TYPE:
            raise ValueError(f'Module 2 chỉ nhận question_type = "{OPEN_QUESTION_TYPE}"')
        return v

    # @field_validator("question_count")
    # @classmethod
    # def check_question_count(cls, v:int) -> int:
    #     if v != OPE

# 3. CLASS OpenQuestion
#
# Các trường:
# - question_id: str
# - content: str
# - answer_hint: str
# - evaluation_criteria: list[str]
#
# Ý nghĩa:
# question_id:
#     ID câu hỏi.
#
# content:
#     Nội dung câu hỏi cần trẻ trả lời.
#
# answer_hint:
#     Gợi ý cách trả lời.
#
# evaluation_criteria:
#     Các tiêu chí dùng để đánh giá câu trả lời.
#
# TODO:
# - Kiểm tra content không rỗng.
# - Kiểm tra danh sách tiêu chí hợp lệ.
# - Kiểm tra dữ liệu dạng string/list đúng schema.


class OpenQuestion(_Base):
    question_id : str = Field(..., min_length=1) #id câu hỏi 
    content: str = Field(..., min_length=1) #nội dung câu hoi, không được rỗng
    answer_hint: str = "" #gợi ý cách trả ời, cho phép rỗng
    evaluation_criteria: list[str] = Field(..., min_length=1) #tiêu chí chấm bài, ít nhất 1 tiêu chí

    @field_validator("evaluation_criteria")
    @classmethod
    def check_criteria(cls, v: list[str]) -> list[str]:
        cleaned = [c.strip() for c in v if c and c.strip()] # bỏ tiêu chí rỗng
        if not cleaned:
            raise ValueError("evaluation_criteria phải có ít nhất 1 tiêu chí không rỗng")
        return cleaned

# 4. CLASS OpenExerciseData
#
# Các trường:
# - exercise_id: str
# - question_type: str
# - questions: list[OpenQuestion]

class OpenExerciseData(_Base):
    exercise_id:str = Field(..., min_length=1) 
    question_type: str 
    questions: list[OpenQuestion] = Field(..., min_length=1)

# 5. CLASS OpenGenerateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: OpenExerciseData

class OpenGenerateResponse(_Base):
    success: bool = True
    message: str = "Sinh câu hỏi thành công"
    data: OpenExerciseData 
    

# 6. CLASS OpenEvaluateRequest
#
# Dữ liệu FE gửi lên khi yêu cầu đánh giá:
#
# - child_id: int
# - question_id: str
# - question: str
# - answer: str
# - evaluation_criteria: list[str]
# - subject: str
# - topic: str
# - level: str
#
# TODO:
# - Kiểm tra các trường bắt buộc.
# - Không cho phép answer rỗng.
# - Giới hạn độ dài question, answer và topic.
# - Kiểm tra evaluation_criteria đúng kiểu dữ liệu.
# - Kiểm tra level hợp lệ.
#
# Lưu ý:
# FE gửi lại câu hỏi và tiêu chí để chấm.
# Backend không bắt buộc lưu câu hỏi vào Database.

class OpenEvaluateRequest(_Base):
    child_id : int = Field(..., gt=0) 
    question_id: str = Field(..., min_length = 1)
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1 , max_length=1000) 
    evaluation_criteria: list[str] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1 , max_length=100)
    topic: str = Field(..., min_length=1 , max_length=100)
    level: str 

    @field_validator("level")
    @classmethod
    def check_level(cls,v :str) -> str:
        if v not in SUPPORTED_LEVELS:
            raise ValueError(f"Level không hợp lệ, Chỉ nhận: {', '.join(SUPPORTED_LEVELS)}")
        return v

    @field_validator("evaluation_criteria")
    @classmethod
    def check_criteria(cls,v :list[str]) -> list[str]:
        cleaned = [c.strip() for c in v if c and c.strip()]
        if not cleaned:
            raise ValueError("evaluation_criteria phải có ít nhất 1 tiêu chí không rỗng")
        return cleaned


# 7. CLASS OpenEvaluationData
#
# Các trường:
# - question_id: str
# - score: float
# - is_appropriate: bool
# - feedback: str
# - strengths: list[str]
# - suggestions: list[str]
# - sample_answer: str
#
# TODO:
# - Kiểm tra score nằm trong [0, 10].
# - Kiểm tra is_appropriate là boolean.
# - Kiểm tra các trường nhận xét đúng kiểu.
# - Giữ toàn bộ nội dung phản hồi bằng tiếng Việt.

class OpenEvaluationData(_Base):
    question_id: str 
    score:float = Field(..., ge=0, le=10) # điểm phải nằm trong [0 ,10]
    is_appropriate: bool # câu trả lời có phù hợp không
    feedback: str = Field(...,min_length=1) # nhận xét tiếng Việt, bắt buộc
    strengths: list[str] = Field(default_factory=list)
    suggestions: list[str]  # gợi ý cải thiện, bắt buộc có trường này
    sample_answer: str=""  # câu trả lời mẫu, cho phép rỗng


# 8. CLASS OpenEvaluateResponse
#
# Các trường:
# - success: bool
# - message: str
# - data: OpenEvaluationData

class OpenEvaluateResponse(_Base):
    success: bool = True 
    message: str = "Đánh giá câu trả lời thành công"
    data: OpenEvaluationData
# 9. KIỂM TRA
#
# TODO:
# - Sinh câu hỏi với question_count hợp lệ.
# - Thiếu evaluation_criteria.
# - Câu trả lời rỗng.
# - Điểm số nhỏ hơn 0 hoặc lớn hơn 10.
# - Model trả score dưới dạng chuỗi không hợp lệ.
# - Model trả thiếu feedback hoặc suggestions.



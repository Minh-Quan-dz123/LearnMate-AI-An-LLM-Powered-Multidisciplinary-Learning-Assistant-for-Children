
"""
Module 3 V3 — Pydantic schema.
Không thay đổi schema detective.py V2.
"""

from __future__ import annotations

import math
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.schemas.detective import (
    TOPIC_NAMES,
    SCENE_SLOTS,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class Region(StrictModel):
    """Bounding box phần trăm của ảnh thật."""

    x: float
    y: float
    width: float
    height: float
    shape: Literal["circle", "rect"] = "rect"

    @model_validator(mode="after")
    def check_box(self):
        values = (
            self.x, self.y,
            self.width, self.height,
        )

        if not all(math.isfinite(v) for v in values):
            raise ValueError("Tọa độ không hợp lệ")

        if (
            self.x < 0 or self.y < 0
            or self.width <= 0
            or self.height <= 0
        ):
            raise ValueError("Kích thước vùng không hợp lệ")

        if self.x + self.width > 100:
            raise ValueError("Vùng vượt chiều ngang ảnh")

        if self.y + self.height > 100:
            raise ValueError("Vùng vượt chiều dọc ảnh")

        area = self.width * self.height

        if not 2 <= area <= 5500:
            raise ValueError(
                "Vùng khoanh quá nhỏ hoặc quá lớn"
            )

        return self


class DraftHint(StrictModel):
    """Gợi ý do Gemini Text sinh, chưa có tọa độ."""

    id: str = Field(min_length=1, max_length=50)
    order: int = Field(ge=1, le=3)

    title: str = Field(min_length=2, max_length=90)
    content: str = Field(min_length=10, max_length=350)

    visual_target: str = Field(
        min_length=5,
        max_length=300,
    )


class CaseHint(DraftHint):
    """Gợi ý đã được Vision xác nhận vùng."""

    region: Region


class Hypothesis(StrictModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=2, max_length=150)


class Solution(StrictModel):
    hypothesis_id: str = Field(
        min_length=1,
        max_length=64,
    )

    accepted_meanings: list[str] = Field(
        min_length=1,
        max_length=8,
    )

    min_recommended_hints: int = Field(
        ge=1,
        le=3,
    )

    explanation: str = Field(
        min_length=30,
        max_length=1000,
    )


class DraftCase(StrictModel):
    """
    Kịch bản ban đầu từ Gemini Text.
    Không chứa tọa độ đoán trước.
    """

    schema_version: Literal[3] = 3
    topic_id: str

    title: str = Field(
        min_length=5,
        max_length=160,
    )

    introduction: str = Field(
        min_length=20,
        max_length=650,
    )

    scene_id: str

    background_prompt: str = Field(
        min_length=50,
        max_length=1800,
    )

    hints: list[DraftHint] = Field(
        min_length=1,
        max_length=3,
    )

    hypotheses: list[Hypothesis] = Field(
        min_length=3,
        max_length=3,
    )

    solution: Solution

    feedback_if_wrong: str = Field(
        min_length=10,
        max_length=300,
    )

    feedback_if_correct: str = Field(
        min_length=10,
        max_length=300,
    )

    @model_validator(mode="after")
    def check_logic(self):
        if self.topic_id not in TOPIC_NAMES:
            raise ValueError("Chủ đề không hợp lệ")

        if self.scene_id not in SCENE_SLOTS:
            raise ValueError("Hiện trường không hợp lệ")

        orders = [h.order for h in self.hints]

        if orders != list(range(1, len(self.hints) + 1)):
            raise ValueError(
                "Thứ tự gợi ý phải liên tục từ 1"
            )

        hint_ids = [h.id for h in self.hints]

        if len(set(hint_ids)) != len(hint_ids):
            raise ValueError("ID gợi ý bị trùng")

        hypothesis_ids = [
            h.id for h in self.hypotheses
        ]

        if len(set(hypothesis_ids)) != 3:
            raise ValueError("ID giả thuyết bị trùng")

        if (
            self.solution.hypothesis_id
            not in hypothesis_ids
        ):
            raise ValueError("Đáp án chuẩn không tồn tại")

        if (
            self.solution.min_recommended_hints
            > len(self.hints)
        ):
            raise ValueError(
                "Số gợi ý khuyến nghị vượt giới hạn"
            )

        return self


class DetectiveCaseV3(DraftCase):
    """
    Kịch bản hoàn chỉnh.

    Mỗi hint có region do Vision xác nhận.
    """

    hints: list[CaseHint] = Field(
        min_length=1,
        max_length=3,
    )


class GenerateRequestV3(StrictModel):
    child_id: int = Field(gt=0)

    topic_id: str = Field(
        min_length=1,
        max_length=40,
    )


class ChildRequestV3(StrictModel):
    child_id: int = Field(gt=0)


class HintRequest(ChildRequestV3):
    request_id: UUID


class SolveRequestV3(ChildRequestV3):
    answer_mode: Literal["choice", "open"]
    submission_id: UUID

    hypothesis_id: str | None = Field(
        default=None,
        max_length=64,
    )

    answer_text: str | None = Field(
        default=None,
        max_length=1000,
    )

    @model_validator(mode="after")
    def check_answer(self):
        if self.answer_mode == "choice":
            if not self.hypothesis_id:
                raise ValueError(
                    "Con hãy chọn một giả thuyết"
                )

            if self.answer_text is not None:
                raise ValueError(
                    "Không gửi text trong chế độ choice"
                )

        else:
            if (
                not self.answer_text
                or not self.answer_text.strip()
            ):
                raise ValueError(
                    "Con hãy viết kết luận trước khi nộp"
                )

            if self.hypothesis_id is not None:
                raise ValueError(
                    "Không gửi giả thuyết ở chế độ open"
                )

            if any(
                ord(c) < 32 and c not in "\n\t"
                for c in self.answer_text
            ):
                raise ValueError(
                    "Câu trả lời chứa ký tự không hợp lệ"
                )

        return self


class VisionBox(StrictModel):
    x: float
    y: float
    width: float
    height: float


class VisionTarget(StrictModel):
    hint_id: str
    visible: bool

    box: VisionBox | None = None

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    observation: str = Field(
        default="",
        max_length=500,
    )


class VisionResult(StrictModel):
    targets: list[VisionTarget] = Field(
        min_length=1,
        max_length=3,
    )


class OpenAssessment(StrictModel):
    """
    Kết quả Gemini đánh giá câu trả lời mở.
    """

    is_correct: bool

    reasoning_support: Literal[
        "strong",
        "partial",
        "insufficient",
    ]

    feedback: str = Field(
        min_length=10,
        max_length=450,
    )

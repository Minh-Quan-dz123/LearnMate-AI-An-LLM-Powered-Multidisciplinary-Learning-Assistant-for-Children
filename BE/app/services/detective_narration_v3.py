
"""
LEARNMATE AI — MODULE 3 V3
Gemini TTS narration.

Chỉ lấy nội dung từ Backend:
- Giới thiệu vụ án.
- Nhận xét sau lần trả lời sai đầu tiên.
- Nhận xét và giải thích sau khi kết thúc.

Không dùng Gemini TTS cho các gợi ý.
Không đọc lời giải khi vụ án chưa kết thúc.
"""

from __future__ import annotations

from app.schemas.detective_v3 import DetectiveCaseV3
from app.services.detective_engine import InvalidActionError
from app.services.detective_v3 import normalize_state


def narration_text_v3(
    case: DetectiveCaseV3,
    raw_state: dict,
    segment_type: str,
    segment_id: str | None,
) -> str:
    """
    Chọn nội dung được phép gửi đến Gemini TTS.

    Parameters:
        case: Kịch bản V3.
        raw_state: Trạng thái chơi trong Supabase.
        segment_type: Loại nội dung muốn đọc.
        segment_id: V3 không sử dụng.

    Returns:
        Văn bản tiếng Việt cho Gemini đọc.

    Raises:
        InvalidActionError nếu nội dung chưa được mở khóa.
    """

    state = normalize_state(raw_state)

    if segment_id is not None:
        raise InvalidActionError(
            "Lời kể V3 không nhận segment_id."
        )

    # 1. Giới thiệu: được đọc ngay khi vào vụ án.
    if segment_type == "introduction":
        return f"{case.title}. {case.introduction}"

    # 2. Các loại còn lại chỉ được đọc
    #    khi trẻ đã nộp ít nhất một kết luận.
    last = state.get("last_submission_result")

    if not isinstance(last, dict):
        raise InvalidActionError(
            "Chưa có kết luận để cô giáo nhận xét."
        )

    feedback = last.get("feedback", "")

    if (
        not isinstance(feedback, str)
        or not feedback.strip()
    ):
        raise InvalidActionError(
            "Chưa có phản hồi để đọc."
        )

    # 3. Sai lần đầu: chỉ đọc nhận xét.
    #    Không tiết lộ nguyên nhân khoa học.
    if segment_type == "retry_feedback":
        if (
            state["completed"]
            or state["attempts_used"] != 1
        ):
            raise InvalidActionError(
                "Chưa có lời nhận xét lượt đầu."
            )

        return feedback

    # 4. Kết thúc vụ án: đọc phản hồi
    #    và giải thích khoa học.
    if segment_type == "final_explanation":
        if not state["completed"]:
            raise InvalidActionError(
                "Chưa thể đọc lời giải "
                "trước khi kết thúc."
            )

        return (
            f"{feedback} "
            f"Lời giải khoa học: "
            f"{case.solution.explanation}"
        )

    raise InvalidActionError(
        "V3 chỉ hỗ trợ giới thiệu "
        "và phản hồi kết luận."
    )

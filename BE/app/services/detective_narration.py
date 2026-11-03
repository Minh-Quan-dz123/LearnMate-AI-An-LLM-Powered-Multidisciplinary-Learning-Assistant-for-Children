
"""
Module 3 — Gemini TTS.

Chỉ tạo giọng đọc từ nội dung có sẵn ở Backend.
Không lấy text tự do từ Frontend.

Không cho đọc lời giải hoặc manh mối chưa mở khóa.
"""

from __future__ import annotations

import asyncio
import hashlib

from app.schemas.detective import DetectiveCase

from app.services.detective_engine import (
    normalize_state,
    InvalidActionError,
)


ALLOWED_SEGMENTS = frozenset({
    "introduction",
    "clue",
    "experiment",
    "retry_feedback",
    "final_explanation",
})


def narration_text(
    case: DetectiveCase,
    state: dict,
    segment_type: str,
    segment_id: str | None,
) -> str:
    state = normalize_state(state)

    if segment_type not in ALLOWED_SEGMENTS:
        raise InvalidActionError(
            "Đoạn giọng kể không hợp lệ."
        )

    # Giới thiệu.
    if segment_type == "introduction":
        if segment_id is not None:
            raise InvalidActionError(
                "Đoạn giới thiệu không có ID."
            )

        return f"{case.title}. {case.introduction}"

    # Manh mối.
    if segment_type == "clue":
        if segment_id not in state["discovered_clue_ids"]:
            raise InvalidActionError(
                "Manh mối này chưa được khám phá."
            )

        clue = next(
            (
                c for c in case.clues
                if c.id == segment_id
            ),
            None,
        )

        if clue is None:
            raise InvalidActionError(
                "Không tìm thấy manh mối."
            )

        return f"{clue.title}. {clue.description}"

    # Thử nghiệm.
    if segment_type == "experiment":
        if segment_id not in state[
            "completed_experiment_ids"
        ]:
            raise InvalidActionError(
                "Thử nghiệm này chưa thực hiện."
            )

        experiment = next(
            (
                e for e in case.experiments
                if e.id == segment_id
            ),
            None,
        )

        if experiment is None:
            raise InvalidActionError(
                "Không tìm thấy thử nghiệm."
            )

        return f"{experiment.label}. {experiment.result}"

    if segment_id is not None:
        raise InvalidActionError(
            "Đoạn này không nhận ID."
        )

    # Gợi ý sau lần sai đầu.
    if segment_type == "retry_feedback":
        if (
            state["completed"]
            or state["attempts_used"] != 1
        ):
            raise InvalidActionError(
                "Chưa có lời gợi ý để đọc."
            )

        return (
            state["last_feedback"]
            or case.feedback_if_wrong
        )

    # Lời giải: chỉ sau khi đã kết thúc.
    if not state["completed"]:
        raise InvalidActionError(
            "Vụ án chưa kết thúc; "
            "chưa thể đọc lời giải."
        )

    feedback = (
        case.feedback_if_correct
        if state["outcome"] == "solved"
        else state["last_feedback"]
        or "Cùng cô xem lời giải nhé!"
    )

    return f"{feedback} {case.solution.explanation}"


def audio_cache_key(
    segment_type: str,
    segment_id: str | None,
    voice: str,
    text: str,
) -> str:
    content_hash = hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()[:20]

    return (
        f"{segment_type}:"
        f"{segment_id or '-'}:"
        f"{voice}:"
        f"{content_hash}"
    )


# Lock nội bộ cho demo một Backend worker.
_case_locks: dict[str, asyncio.Lock] = {}


def narration_lock(case_id: str) -> asyncio.Lock:
    return _case_locks.setdefault(
        case_id,
        asyncio.Lock(),
    )

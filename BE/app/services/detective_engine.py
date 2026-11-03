
"""
Module 3 — Game Engine v2.

- Chỉ chấm hypothesis_id.
- Evidence không bắt buộc.
- Tối đa 2 lượt.
- Sai lần 2 vẫn hoàn thành.
- Không gửi lời giải trước khi kết thúc.
"""

from __future__ import annotations

import json

from app.schemas.detective import (
    DetectiveCase,
    PublicClue,
    PublicClueVisual,
    to_public_case,
)

from app.services.detective_storage import (
    public_image_url,
)


class InvalidActionError(ValueError):
    pass


def initial_play_state() -> dict:
    return {
        "discovered_clue_ids": [],
        "completed_experiment_ids": [],
        "selected_hypothesis_id": None,
        "completed": False,
        "attempts_used": 0,
        "outcome": None,
        "last_submission": None,
        "last_submission_id": None,
        "last_feedback": None,
    }


def normalize_state(
    state: dict | None,
) -> dict:
    """
    Chuẩn hóa state và hỗ trợ dữ liệu v1.1.
    """
    result = initial_play_state()

    if not isinstance(state, dict):
        return result

    for field in (
        "discovered_clue_ids",
        "completed_experiment_ids",
    ):
        if isinstance(state.get(field), list):
            result[field] = list(dict.fromkeys(
                value
                for value in state[field]
                if isinstance(value, str)
            ))

    if isinstance(
        state.get("selected_hypothesis_id"), str
    ):
        result["selected_hypothesis_id"] = (
            state["selected_hypothesis_id"]
        )

    finished = state.get("completed") is True

    used = state.get("attempts_used")

    result["attempts_used"] = (
        min(2, max(0, used))
        if type(used) is int
        else (1 if finished else 0)
    )

    result["completed"] = finished

    if finished:
        outcome = state.get("outcome")

        result["outcome"] = (
            outcome
            if outcome in ("solved", "unsolved")
            else "solved"
        )

    for field in (
        "last_submission",
        "last_submission_id",
        "last_feedback",
    ):
        if isinstance(state.get(field), str):
            result[field] = state[field]

    return result


def public_clue(
    clue,
    manifest: dict | None = None,
    case: DetectiveCase | None = None,
) -> dict:
    """
    Tạo dữ liệu công khai của một clue đã mở.
    """
    path = (
        (manifest or {})
        .get("clue_images", {})
        .get(clue.id)
    )

    spec = clue.visual_spec

    reference_asset = (
        next(
            (
                o.asset_id
                for o in case.objects
                if o.clue_id == clue.id
            ),
            None,
        )
        if case
        else None
    )

    visual = None

    if spec:
        visual = PublicClueVisual(
            kind=spec.kind,
            image_url=(
                public_image_url(path)
                if isinstance(path, str) and path
                else None
            ),
            highlight=spec.highlight,
            reference_asset_id=reference_asset,
            alt=f"Minh họa: {clue.title}",
        )

    return PublicClue(
        id=clue.id,
        title=clue.title,
        description=clue.description,
        visual=visual,
        reference_asset_id=reference_asset,
    ).model_dump(mode="json")


def inspect_object(
    case: DetectiveCase,
    state: dict,
    object_id: str,
    manifest: dict | None = None,
) -> tuple[dict, dict]:
    obj = next(
        (
            o for o in case.objects
            if o.object_id == object_id
        ),
        None,
    )

    if obj is None:
        raise InvalidActionError(
            "Vật thể này không có trong hiện trường."
        )

    clue = next(
        c for c in case.clues
        if c.id == obj.clue_id
    )

    next_state = normalize_state(state)

    already = (
        clue.id in next_state["discovered_clue_ids"]
    )

    if not already:
        next_state["discovered_clue_ids"].append(
            clue.id
        )

    return next_state, {
        "clue": public_clue(clue, manifest, case),
        "discovered_clue_ids":
            next_state["discovered_clue_ids"],
        "already_discovered": already,
    }


def run_experiment(
    case: DetectiveCase,
    state: dict,
    experiment_id: str,
    manifest: dict | None = None,
) -> tuple[dict, dict]:
    experiment = next(
        (
            e for e in case.experiments
            if e.id == experiment_id
        ),
        None,
    )

    if experiment is None:
        raise InvalidActionError(
            "Thử nghiệm không thuộc vụ án này."
        )

    next_state = normalize_state(state)

    already = (
        experiment.id
        in next_state["completed_experiment_ids"]
    )

    if not already:
        next_state["completed_experiment_ids"].append(
            experiment.id
        )

    clue = next(
        c for c in case.clues
        if c.id == experiment.unlocks_clue_id
    )

    if clue.id not in next_state["discovered_clue_ids"]:
        next_state["discovered_clue_ids"].append(
            clue.id
        )

    return next_state, {
        "result": experiment.result,
        "unlocked_clue": public_clue(
            clue, manifest, case
        ),
        "already_completed": already,
        "discovered_clue_ids":
            next_state["discovered_clue_ids"],
        "completed_experiment_ids":
            next_state["completed_experiment_ids"],
    }


def _signature(
    hypothesis_id: str,
    evidence_ids: list[str],
) -> str:
    return json.dumps(
        [
            hypothesis_id,
            sorted(evidence_ids),
        ],
        separators=(",", ":"),
    )


def final_result(
    case: DetectiveCase,
    state: dict,
) -> dict:
    state = normalize_state(state)

    if not state["completed"]:
        raise InvalidActionError(
            "Vụ án chưa kết thúc."
        )

    outcome = state["outcome"]

    return {
        "completed": True,
        "outcome": outcome,
        "attempts_used": state["attempts_used"],
        "remaining_attempts": 0,
        "can_retry": False,
        "title": case.title,
        "feedback": (
            case.feedback_if_correct
            if outcome == "solved"
            else (
                state["last_feedback"]
                or "Vụ án đã khép lại. Cùng cô xem lời giải nhé!"
            )
        ),
        "explanation": case.solution.explanation,
    }


def solve_case(
    case: DetectiveCase,
    state: dict,
    hypothesis_id: str,
    evidence_ids: list[str],
    submission_id: str | None = None,
) -> tuple[dict, dict]:
    """
    Đúng/sai chỉ phụ thuộc giả thuyết.

    submission_id giúp phân biệt:
      - Retry request cũ.
      - Lượt chơi mới có cùng giả thuyết.
    """

    if hypothesis_id not in {
        h.id for h in case.hypotheses
    }:
        raise InvalidActionError(
            "Giả thuyết này không thuộc vụ án."
        )

    next_state = normalize_state(state)

    available = set(
        next_state["discovered_clue_ids"]
    )

    if (
        len(evidence_ids) != len(set(evidence_ids))
        or not set(evidence_ids).issubset(available)
    ):
        raise InvalidActionError(
            "Con chỉ có thể chọn manh mối "
            "hợp lệ đã khám phá, không trùng ID."
        )

    if next_state["completed"]:
        return next_state, final_result(
            case, next_state
        )

    signature = _signature(
        hypothesis_id, evidence_ids
    )

    if submission_id is not None:
        is_duplicate = (
            submission_id ==
            next_state["last_submission_id"]
        )
    else:
        is_duplicate = (
            signature ==
            next_state["last_submission"]
        )

    if is_duplicate:
        return next_state, {
            "completed": False,
            "outcome": None,
            "attempts_used":
                next_state["attempts_used"],
            "remaining_attempts":
                2 - next_state["attempts_used"],
            "can_retry": True,
            "feedback": (
                next_state["last_feedback"]
                or case.feedback_if_wrong
            ),
        }

    if next_state["attempts_used"] >= 2:
        raise InvalidActionError(
            "Con đã dùng hết hai lượt kết luận."
        )

    next_state["attempts_used"] += 1
    next_state["selected_hypothesis_id"] = hypothesis_id

    next_state["last_submission"] = signature
    next_state["last_submission_id"] = submission_id

    correct = (
        hypothesis_id ==
        case.solution.hypothesis_id
    )

    finished = (
        correct
        or next_state["attempts_used"] == 2
    )

    next_state["completed"] = finished

    next_state["outcome"] = (
        "solved" if correct else "unsolved"
    ) if finished else None

    if correct:
        feedback = case.feedback_if_correct
    elif finished:
        feedback = (
            "Con đã quan sát rất chăm chỉ. "
            "Cùng cô xem lời giải nhé!"
        )
    else:
        feedback = case.feedback_if_wrong

    next_state["last_feedback"] = feedback

    if finished:
        return next_state, final_result(
            case, next_state
        )

    return next_state, {
        "completed": False,
        "outcome": None,
        "attempts_used": 1,
        "remaining_attempts": 1,
        "can_retry": True,
        "feedback": feedback,
    }


def public_case_with_state(
    case: DetectiveCase,
    *,
    case_id: str,
    image_url: str,
    state: dict,
    manifest: dict | None = None,
) -> dict:
    """
    Chỉ trả dữ liệu FE được quyền xem.
    """

    public = to_public_case(
        case,
        case_id=case_id,
        image_url=image_url,
    ).model_dump(mode="json")

    state = normalize_state(state)

    discovered = set(
        state["discovered_clue_ids"]
    )

    public["discovered_clues"] = [
        public_clue(c, manifest, case)
        for c in case.clues
        if c.id in discovered
    ]

    public["discovered_clue_ids"] = [
        c.id
        for c in case.clues
        if c.id in discovered
    ]

    public["experiments"] = [
        {
            "id": e.id,
            "label": e.label,
        }
        for e in case.experiments
    ]

    public["completed_experiment_ids"] = [
        e.id
        for e in case.experiments
        if e.id in state["completed_experiment_ids"]
    ]

    public["selected_hypothesis_id"] = (
        state["selected_hypothesis_id"]
    )

    public["completed"] = state["completed"]
    public["attempts_used"] = state["attempts_used"]
    public["outcome"] = state["outcome"]

    public["retry_feedback"] = (
        state["last_feedback"]
        if (
            state["attempts_used"] == 1
            and not state["completed"]
        )
        else None
    )

    return public

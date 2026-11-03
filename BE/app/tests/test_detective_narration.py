
import pytest

from app.services.detective_narration import (
    narration_text,
    audio_cache_key,
)

from app.services.detective_engine import (
    initial_play_state,
    solve_case,
    InvalidActionError,
)

from test_detective_v2 import sample_case


def test_intro_never_contains_solution():
    case = sample_case()

    text = narration_text(
        case,
        initial_play_state(),
        "introduction",
        None,
    )

    assert case.title in text
    assert case.solution.explanation not in text


def test_locked_clue_and_experiment():
    case = sample_case()

    with pytest.raises(InvalidActionError):
        narration_text(
            case,
            initial_play_state(),
            "clue",
            "c1",
        )

    with pytest.raises(InvalidActionError):
        narration_text(
            case,
            initial_play_state(),
            "experiment",
            "e1",
        )


def test_unlocked_clue():
    case = sample_case()

    state = initial_play_state()
    state["discovered_clue_ids"] = ["c1"]

    text = narration_text(
        case,
        state,
        "clue",
        "c1",
    )

    assert "Lá bị khuyết" in text
    assert "Đáp án khoa học" not in text


def test_retry_narration_no_solution():
    case = sample_case()

    state, _ = solve_case(
        case,
        initial_play_state(),
        "h2",
        [],
    )

    hint = narration_text(
        case,
        state,
        "retry_feedback",
        None,
    )

    assert hint == case.feedback_if_wrong
    assert case.solution.explanation not in hint

    with pytest.raises(InvalidActionError):
        narration_text(
            case,
            state,
            "final_explanation",
            None,
        )


def test_solved_final_and_unsolved_final():
    case = sample_case()

    for first, second in [
        ("h1", None),
        ("h2", "h3"),
    ]:
        state, _ = solve_case(
            case,
            initial_play_state(),
            first,
            [],
        )

        if second:
            state, _ = solve_case(
                case,
                state,
                second,
                [],
            )

        final = narration_text(
            case,
            state,
            "final_explanation",
            None,
        )

        assert case.solution.explanation in final


def test_audio_key_changes_with_text_and_voice():
    key = audio_cache_key(
        "clue",
        "c1",
        "teacher_vi_v1",
        "Lá bị cắn",
    )

    assert key == audio_cache_key(
        "clue",
        "c1",
        "teacher_vi_v1",
        "Lá bị cắn",
    )

    assert key != audio_cache_key(
        "clue",
        "c1",
        "teacher_vi_v2",
        "Lá bị cắn",
    )

    assert key != audio_cache_key(
        "clue",
        "c1",
        "teacher_vi_v1",
        "Lá bị cắn!",
    )


def test_invalid_segment_id():
    with pytest.raises(InvalidActionError):
        narration_text(
            sample_case(),
            initial_play_state(),
            "introduction",
            "c1",
        )


import pytest

from app.schemas.detective import DetectiveCase

from app.services.detective_engine import (
    InvalidActionError,
    initial_play_state,
    normalize_state,
    solve_case,
    inspect_object,
    public_case_with_state,
    final_result,
)


def sample_case():
    return DetectiveCase.model_validate({
        "topic_id": "plants",
        "title": "Vụ chiếc lá",
        "introduction": "Có dấu lạ.",
        "scene_id": "garden",
        "background_prompt": "A garden",

        "objects": [
            {
                "object_id": "o1",
                "label": "Lá",
                "asset_id": "wilted_plant",
                "slot_id": "center",
                "clue_id": "c1",
            },
            {
                "object_id": "o2",
                "label": "Đất",
                "asset_id": "dry_soil",
                "slot_id": "soil",
                "clue_id": "c2",
            },
            {
                "object_id": "o3",
                "label": "Bình",
                "asset_id": "watering_can",
                "slot_id": "fence",
                "clue_id": "c3",
            },
        ],

        "clues": [
            {
                "id": "c1",
                "title": "Lá bị khuyết",
                "description": "Có vết khuyết",
                "visual_spec": {
                    "kind": "ai_closeup",
                    "subject": "green leaf",
                    "must_show": ["jagged edge"],
                    "must_not_show": ["animal"],
                },
            },
            {
                "id": "c2",
                "title": "Đất khô",
                "description": "Đất ít nước",
            },
            {
                "id": "c3",
                "title": "Bình tưới",
                "description": "Bình nước",
            },
        ],

        "hypotheses": [
            {"id": "h1", "label": "Sâu ăn lá"},
            {"id": "h2", "label": "Thiếu nước"},
            {"id": "h3", "label": "Gió thổi"},
        ],

        "experiments": [
            {
                "id": "e1",
                "label": "Thử đất",
                "result": "Đất khô",
                "unlocks_clue_id": "c2",
            }
        ],

        "solution": {
            "hypothesis_id": "h1",
            "required_evidence_ids": ["c1", "c2"],
            "explanation": "Đáp án khoa học",
        },

        "feedback_if_wrong":
            "Con hãy nhìn lại dấu vết.",
        "feedback_if_correct":
            "Con đã tìm đúng!",
    })


def test_correct_with_zero_evidence():
    state, result = solve_case(
        sample_case(),
        initial_play_state(),
        "h1",
        [],
    )

    assert result["completed"]
    assert result["outcome"] == "solved"
    assert state["attempts_used"] == 1


def test_wrong_then_correct():
    case = sample_case()

    state, first = solve_case(
        case,
        initial_play_state(),
        "h2",
        [],
    )

    assert not first["completed"]
    assert first["attempts_used"] == 1
    assert "explanation" not in first

    state, second = solve_case(
        case,
        state,
        "h1",
        [],
    )

    assert second["completed"]
    assert second["outcome"] == "solved"
    assert second["attempts_used"] == 2


def test_wrong_wrong_and_repeated_request():
    case = sample_case()

    state, first = solve_case(
        case,
        initial_play_state(),
        "h2",
        [],
        "submit-0001",
    )

    repeated_state, repeated = solve_case(
        case,
        state,
        "h2",
        [],
        "submit-0001",
    )

    assert repeated_state == state
    assert repeated["attempts_used"] == 1

    same_state, same = solve_case(
        case,
        state,
        "h2",
        [],
        "submit-0002",
    )

    assert same["completed"]
    assert same["outcome"] == "unsolved"

    state, second = solve_case(
        case,
        state,
        "h3",
        [],
        "submit-0003",
    )

    assert second["completed"]
    assert second["outcome"] == "unsolved"

    assert (
        final_result(case, state)["outcome"]
        == "unsolved"
    )


def test_fake_evidence_no_attempt_burn():
    case = sample_case()

    with pytest.raises(InvalidActionError):
        solve_case(
            case,
            initial_play_state(),
            "h1",
            ["c1"],
        )

    with pytest.raises(InvalidActionError):
        solve_case(
            case,
            initial_play_state(),
            "h1",
            ["not_a_clue"],
        )


def test_public_only_unlocked_clue_image(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.detective_engine.public_image_url",
        lambda path: f"https://test/{path}",
    )

    case = sample_case()

    manifest = {
        "clue_images": {
            "c1": "child-101/secret.png",
        }
    }

    public = public_case_with_state(
        case,
        case_id="id",
        image_url="scene",
        state=initial_play_state(),
        manifest=manifest,
    )

    assert "secret.png" not in str(public)
    assert "solution" not in public
    assert "visual_spec" not in str(public)

    next_state, found = inspect_object(
        case,
        initial_play_state(),
        "o1",
        manifest,
    )

    assert (
        found["clue"]["visual"]["image_url"]
        is not None
    )


def test_legacy_state():
    state = normalize_state({
        "completed": True,
        "discovered_clue_ids": ["c1"],
    })

    assert state["completed"]
    assert state["outcome"] == "solved"
    assert state["attempts_used"] == 1
    assert initial_play_state()["outcome"] is None

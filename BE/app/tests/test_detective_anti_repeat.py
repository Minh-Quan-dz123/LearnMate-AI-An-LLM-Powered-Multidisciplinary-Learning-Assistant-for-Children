
"""Chạy: python -m pytest tests/test_detective_anti_repeat.py -q"""
import json
import asyncio
import pytest

from app.egm.detective_egm import (
    build_detective_prompt,
    compact_recent_cases,
    generate_detective_case,
    InvalidCaseOutputError,
)


def sample_case(
    title="Bí ẩn chậu cây bị héo",
    intro="Chậu cây trong lớp héo đi qua một đêm.",
    explanation="Cây héo vì hai ngày không được tưới nước."
):
    """Fixture vụ án tối thiểu đúng luật: mọi clue đều mở khóa được."""
    return {
        "topic_id": "plants",
        "title": title,
        "introduction": intro,
        "scene_id": "classroom",
        "background_prompt": "Bright empty classroom, 2D cartoon",
        "objects": [
            {
                "object_id": "plant",
                "label": "Chậu cây",
                "asset_id": "wilted_plant",
                "slot_id": "desk_left",
                "clue_id": "leaves"
            },
            {
                "object_id": "soil",
                "label": "Đất",
                "asset_id": "dry_soil",
                "slot_id": "desk_right",
                "clue_id": "soil"
            },
            {
                "object_id": "book",
                "label": "Sổ",
                "asset_id": "notebook",
                "slot_id": "shelf",
                "clue_id": "book"
            },
        ],
        "clues": [
            {"id": "leaves", "title": "Lá", "description": "Lá hơi rũ."},
            {"id": "soil", "title": "Đất", "description": "Đất khô."},
            {"id": "book", "title": "Sổ", "description": "Lịch tưới bị bỏ quên."},
        ],
        "hypotheses": [
            {"id": "water", "label": "Thiếu nước"},
            {"id": "light", "label": "Thiếu sáng"},
            {"id": "bugs", "label": "Sâu bệnh"},
        ],
        "experiments": [
            {
                "id": "check",
                "label": "Đo độ ẩm",
                "result": "Đất khô",
                "unlocks_clue_id": "soil"
            },
        ],
        "solution": {
            "hypothesis_id": "water",
            "required_evidence_ids": ["soil", "book"],
            "explanation": explanation,
        },
        "feedback_if_wrong": "Thử tìm thêm manh mối!",
        "feedback_if_correct": "Con giỏi lắm!",
    }


def as_row(data):
    return {
        "topic_id": data["topic_id"],
        "title": data["title"],
        "case_data": data
    }


def test_only_same_topic_in_last_five():
    old = sample_case()

    rows = [
        as_row(old),
        as_row({**old, "topic_id": "weather"}),
        as_row(old),
        as_row({**old, "topic_id": "space"}),
        as_row(old),
        as_row(old)
    ]

    # Phần tử thứ 6 phải bị bỏ qua.
    result = compact_recent_cases(rows, topic_id="plants")

    assert len(result) == 3
    assert result[0]["title"] == old["title"]

    prompt = build_detective_prompt(
        topic_id="plants",
        age=8,
        previous_cases=result
    )

    assert "Bí ẩn chậu cây bị héo" in prompt
    assert "Không được sao chép" in prompt


def test_duplicate_is_regenerated():
    old = sample_case()

    new = sample_case(
        title="Bí ẩn hạt giống chưa nảy mầm",
        intro="Tại góc vườn, hạt giống nằm im dù đã qua nhiều ngày.",
        explanation="Hạt chưa nảy mầm vì thiếu độ ẩm phù hợp trong đất.",
    )

    # Vụ mới phải khác cả manh mối và nguyên nhân,
    # không chỉ đổi title.
    new["clues"][0]["title"] = "Hạt khô"
    new["clues"][1]["title"] = "Bông ẩm"
    new["clues"][2]["title"] = "Nhật ký gieo hạt"
    new["hypotheses"][0]["label"] = "Hạt thiếu độ ẩm"

    prompts = []

    async def fake_llm(**kwargs):
        prompts.append(kwargs["prompt"])

        assert kwargs["model"] == "detective"

        return json.dumps(
            old if len(prompts) == 1 else new,
            ensure_ascii=False
        )

    generated = asyncio.run(
        generate_detective_case(
            topic_id="plants",
            age=8,
            recent_cases=[as_row(old)],
            llm_call=fake_llm,
            max_attempts=2,
        )
    )

    assert generated.title == new["title"]
    assert len(prompts) == 2
    assert old["title"] in prompts[0]


def test_exhaust_retry_fails_not_saving():
    old = sample_case()

    async def fake_llm(**kwargs):
        return json.dumps(old, ensure_ascii=False)

    with pytest.raises(InvalidCaseOutputError):
        asyncio.run(
            generate_detective_case(
                topic_id="plants",
                age=8,
                recent_cases=[as_row(old)],
                llm_call=fake_llm,
                max_attempts=2,
            )
        )


def test_different_topic_not_sent_to_prompt():
    old = sample_case()

    async def fake_llm(**kwargs):
        assert (
            '"title": "Bí ẩn chậu cây bị héo"'
            not in kwargs["prompt"]
        )
        return json.dumps(old, ensure_ascii=False)

    generated = asyncio.run(
        generate_detective_case(
            topic_id="plants",
            age=8,
            recent_cases=[
                as_row({**old, "topic_id": "weather"})
            ],
            llm_call=fake_llm,
        )
    )

    assert generated.title == old["title"]

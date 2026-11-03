
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ==================================================
# CHỦ ĐỀ
# ==================================================

TOPIC_NAMES = {
    "plants": "Thực vật kỳ thú",
    "animals": "Thế giới động vật",
    "environment": "Môi trường xanh",
    "weather": "Bí ẩn thời tiết",
    "physics": "Vật lý quanh ta",
    "water": "Nước và vật chất",
    "space": "Khám phá vũ trụ",
}


# ==================================================
# HIỆN TRƯỜNG VÀ SLOT
# ==================================================

SCENE_SLOTS = {
    "classroom": {
        "desk_left",
        "desk_right",
        "window",
        "shelf",
    },
    "garden": {
        "center",
        "soil",
        "fence",
        "corner",
    },
    "lab": {
        "table_left",
        "table_right",
        "cabinet",
        "window",
    },
}

ALLOWED_ASSETS = {
    "wilted_plant",
    "dry_soil",
    "watering_can",
    "notebook",
    "water_tank",
    "lamp",
    "thermometer",
    "toy_robot",
    "magnifier",
}

TopicId = Literal[
    "plants",
    "animals",
    "environment",
    "weather",
    "physics",
    "water",
    "space",
]

RequestedTopicId = Literal[
    "plants",
    "animals",
    "environment",
    "weather",
    "physics",
    "water",
    "space",
    "random",
]

SceneId = Literal[
    "classroom",
    "garden",
    "lab",
]


class DetectiveBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class GenerateCaseRequest(DetectiveBaseModel):
    child_id: int = Field(gt=0)
    topic_id: str = Field(
        min_length=1,
        max_length=40,
    )


# ==================================================
# SCHEMA NỘI BỘ
# ==================================================

class CaseObject(DetectiveBaseModel):
    object_id: str = Field(
        min_length=1,
        max_length=64,
    )
    label: str = Field(
        min_length=1,
        max_length=120,
    )
    asset_id: str = Field(
        min_length=1,
        max_length=64,
    )
    slot_id: str = Field(
        min_length=1,
        max_length=64,
    )
    clue_id: str = Field(
        min_length=1,
        max_length=64,
    )


class CaseVisualSpec(DetectiveBaseModel):
    kind: Literal[
        "ai_closeup",
        "compare",
        "experiment_effect",
    ] = "ai_closeup"

    subject: str = Field(
        min_length=2,
        max_length=100,
    )

    must_show: list[str] = Field(
        min_length=1,
        max_length=4,
    )

    must_not_show: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    highlight: str | None = Field(
        default=None,
        max_length=60,
    )


class CaseClue(DetectiveBaseModel):
    id: str = Field(
        min_length=1,
        max_length=64,
    )

    title: str = Field(
        min_length=1,
        max_length=120,
    )

    description: str = Field(
        min_length=1,
        max_length=500,
    )

    visual_spec: CaseVisualSpec | None = None


class CaseHypothesis(DetectiveBaseModel):
    id: str = Field(
        min_length=1,
        max_length=64,
    )

    label: str = Field(
        min_length=1,
        max_length=200,
    )


class CaseExperiment(DetectiveBaseModel):
    id: str = Field(
        min_length=1,
        max_length=64,
    )

    label: str = Field(
        min_length=1,
        max_length=200,
    )

    result: str = Field(
        min_length=1,
        max_length=500,
    )

    unlocks_clue_id: str = Field(
        min_length=1,
        max_length=64,
    )


class CaseSolution(DetectiveBaseModel):
    hypothesis_id: str = Field(
        min_length=1,
        max_length=64,
    )

    # Bằng chứng hỗ trợ lời giải,
    # KHÔNG phải điều kiện chấm kết luận.
    required_evidence_ids: list[str] = Field(
        min_length=2,
        max_length=6,
    )

    explanation: str = Field(
        min_length=1,
        max_length=1000,
    )


class DetectiveCase(DetectiveBaseModel):
    topic_id: TopicId

    title: str = Field(
        min_length=1,
        max_length=160,
    )

    introduction: str = Field(
        min_length=1,
        max_length=1200,
    )

    scene_id: SceneId

    background_prompt: str = Field(
        min_length=1,
        max_length=1500,
    )

    objects: list[CaseObject] = Field(
        min_length=3,
        max_length=5,
    )

    clues: list[CaseClue] = Field(
        min_length=3,
        max_length=6,
    )

    hypotheses: list[CaseHypothesis] = Field(
        min_length=3,
        max_length=3,
    )

    experiments: list[CaseExperiment] = Field(
        min_length=1,
        max_length=3,
    )

    solution: CaseSolution

    feedback_if_wrong: str = Field(
        min_length=1,
        max_length=500,
    )

    feedback_if_correct: str = Field(
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_game_rules(self):
        def ensure_unique(
            values: list[str],
            what: str,
        ) -> None:
            if len(values) != len(set(values)):
                raise ValueError(
                    f"{what} bị trùng"
                )

        ensure_unique(
            [o.object_id for o in self.objects],
            "object_id",
        )

        ensure_unique(
            [o.slot_id for o in self.objects],
            "slot_id",
        )

        ensure_unique(
            [c.id for c in self.clues],
            "clue_id",
        )

        ensure_unique(
            [h.id for h in self.hypotheses],
            "hypothesis_id",
        )

        ensure_unique(
            [e.id for e in self.experiments],
            "experiment_id",
        )

        ensure_unique(
            self.solution.required_evidence_ids,
            "required_evidence_ids",
        )

        clue_ids = {
            c.id for c in self.clues
        }

        hypothesis_ids = {
            h.id for h in self.hypotheses
        }

        reachable_clues: set[str] = set()

        # Kiểm tra object/sprite.
        for obj in self.objects:
            if obj.asset_id not in ALLOWED_ASSETS:
                raise ValueError(
                    f"Asset chưa hỗ trợ: {obj.asset_id}"
                )

            if obj.slot_id not in SCENE_SLOTS[
                self.scene_id
            ]:
                raise ValueError(
                    f"Slot không hợp lệ: {obj.slot_id}"
                )

            if obj.clue_id not in clue_ids:
                raise ValueError(
                    "Object trỏ tới clue không tồn tại: "
                    f"{obj.clue_id}"
                )

            reachable_clues.add(obj.clue_id)

        # Kiểm tra thử nghiệm.
        for exp in self.experiments:
            if exp.unlocks_clue_id not in clue_ids:
                raise ValueError(
                    "Experiment trỏ tới clue không tồn tại"
                )

            reachable_clues.add(
                exp.unlocks_clue_id
            )

        if not clue_ids.issubset(reachable_clues):
            raise ValueError(
                "Có manh mối không thể thu thập"
            )

        if (
            self.solution.hypothesis_id
            not in hypothesis_ids
        ):
            raise ValueError(
                "Giả thuyết đúng không tồn tại"
            )

        required = set(
            self.solution.required_evidence_ids
        )

        if not required.issubset(reachable_clues):
            raise ValueError(
                "Bằng chứng hỗ trợ không thể thu thập"
            )

        return self


# ==================================================
# SCHEMA CÔNG KHAI — FE
# ==================================================

class PublicCaseObject(DetectiveBaseModel):
    object_id: str
    label: str
    asset_id: str
    slot_id: str


class PublicCaseExperiment(DetectiveBaseModel):
    id: str
    label: str


class PublicClueVisual(DetectiveBaseModel):
    kind: Literal[
        "ai_closeup",
        "compare",
        "experiment_effect",
    ]

    image_url: str | None = None
    reference_asset_id: str | None = None
    highlight: str | None = None

    alt: str = Field(
        min_length=1,
        max_length=250,
    )


class PublicClue(DetectiveBaseModel):
    id: str
    title: str
    description: str
    reference_asset_id: str | None = None
    visual: PublicClueVisual | None = None


class CasePublicData(DetectiveBaseModel):
    case_id: str
    topic_id: TopicId

    title: str
    introduction: str
    image_url: str
    scene_id: SceneId

    objects: list[PublicCaseObject]
    hypotheses: list[CaseHypothesis]

    discovered_clues: list[PublicClue] = Field(
        default_factory=list,
    )

    experiments: list[PublicCaseExperiment] = Field(
        default_factory=list,
    )

    discovered_clue_ids: list[str] = Field(
        default_factory=list,
    )

    completed_experiment_ids: list[str] = Field(
        default_factory=list,
    )

    selected_hypothesis_id: str | None = None

    completed: bool = False

    attempts_used: int = Field(
        default=0,
        ge=0,
        le=2,
    )

    outcome: Literal[
        "solved",
        "unsolved",
    ] | None = None

    retry_feedback: str | None = None


class GenerateCaseResponse(DetectiveBaseModel):
    success: Literal[True] = True

    message: str = "Vụ án mới đã sẵn sàng!"

    data: CasePublicData


def to_public_case(
    case: DetectiveCase,
    *,
    case_id: str,
    image_url: str,
) -> CasePublicData:
    """
    Loại bỏ solution và các manh mối chưa mở.
    Không gửi model_dump() của DetectiveCase cho FE.
    """

    return CasePublicData(
        case_id=case_id,
        topic_id=case.topic_id,
        title=case.title,
        introduction=case.introduction,
        image_url=image_url,
        scene_id=case.scene_id,

        objects=[
            PublicCaseObject(
                object_id=o.object_id,
                label=o.label,
                asset_id=o.asset_id,
                slot_id=o.slot_id,
            )
            for o in case.objects
        ],

        hypotheses=case.hypotheses,
        discovered_clues=[],
    )

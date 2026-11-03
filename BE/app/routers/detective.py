
from __future__ import annotations

import json
import logging

from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import (
    FileResponse,
    JSONResponse,
)

from postgrest.exceptions import APIError
from pydantic import BaseModel, Field
from supabase import AsyncClient

from app.config import get_settings
from app.database import get_supabase

from app.egm.detective_egm import (
    InvalidCaseOutputError,
    generate_detective_case,
)

from app.llm_client import (
    LLMClientError,
    LLMTimeoutError,
    LLMUnavailableError,
    call_image_generation,
    call_speech_generation,
)

from app.schemas.detective import (
    DetectiveCase,
    GenerateCaseRequest,
    GenerateCaseResponse,
    TOPIC_NAMES,
)

from app.services.detective_engine import (
    InvalidActionError,
    initial_play_state,
    inspect_object,
    normalize_state,
    public_case_with_state,
    run_experiment,
    solve_case,
    final_result,
)

from app.services.detective_storage import (
    DetectiveStorageError,
    background_url,
    remove_case_media,
    upload_background,
    upload_clue_image,
    upload_audio,
    public_image_url,
)

from app.services.detective_narration import (
    narration_text,
    audio_cache_key,
    narration_lock,
)


router = APIRouter(
    prefix="/api/detective",
    tags=["Detective - Module 3"],
)

logger = logging.getLogger(__name__)

STATIC_DIR = (
    Path(__file__).resolve().parents[1]
    / "static"
    / "detective"
)


# ==================================================
# REQUEST SCHEMAS
# ==================================================

class ChildRequest(BaseModel):
    child_id: int = Field(gt=0)


class InspectRequest(ChildRequest):
    object_id: str = Field(
        min_length=1,
        max_length=64,
    )


class ExperimentRequest(ChildRequest):
    experiment_id: str = Field(
        min_length=1,
        max_length=64,
    )


class SolveRequest(ChildRequest):
    submission_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
    )

    hypothesis_id: str = Field(
        min_length=1,
        max_length=64,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
    )


class NarrationRequest(ChildRequest):
    segment_type: Literal[
        "introduction",
        "clue",
        "experiment",
        "retry_feedback",
        "final_explanation",
    ]

    segment_id: str | None = Field(
        default=None,
        max_length=64,
    )


# ==================================================
# RESPONSE HELPERS
# ==================================================

def ok(message: str, data: dict) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error(
    status: int,
    code: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "message": message,
            "error": {
                "code": code,
                "details": None,
            },
        },
    )


def database_error() -> JSONResponse:
    return error(
        503,
        "DATABASE_ERROR",
        "Cơ sở dữ liệu đang bận. Con hãy thử lại nhé!",
    )


def invalid_action(
    exc: InvalidActionError,
) -> JSONResponse:
    return error(
        422,
        "INVALID_ACTION",
        str(exc),
    )


# ==================================================
# DATABASE HELPERS
# ==================================================

async def load_case(
    db: AsyncClient,
    case_id: UUID,
    child_id: int,
) -> dict | None:
    result = await (
        db.table("detective_cases")
        .select("*")
        .eq("id", str(case_id))
        .eq("child_id", child_id)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


async def persist_state(
    db: AsyncClient,
    case_id: UUID,
    state: dict,
) -> None:
    await (
        db.table("detective_cases")
        .update({"play_state": state})
        .eq("id", str(case_id))
        .execute()
    )


async def completed_rows(
    db: AsyncClient,
    child_id: int,
) -> list[dict]:
    result = await (
        db.table("detective_cases")
        .select(
            "id, title, topic_id, image_path, "
            "media_manifest, last_outcome, "
            "last_completed_at, created_at"
        )
        .eq("child_id", child_id)
        .filter("last_completed_at", "not.is", "null")
        .order("last_completed_at", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []


async def trim_history(
    db: AsyncClient,
    child_id: int,
) -> int:
    rows = await completed_rows(db, child_id)

    obsolete = rows[5:]

    if obsolete:
        ids = [
            row["id"]
            for row in obsolete
        ]

        await (
            db.table("detective_cases")
            .delete()
            .in_("id", ids)
            .execute()
        )

        for row in obsolete:
            await remove_case_media(
                row.get("image_path") or "",
                row.get("media_manifest"),
            )

    return min(len(rows), 5)


def parse_stored_case(
    row: dict,
) -> DetectiveCase:
    return DetectiveCase.model_validate(
        row["case_data"]
    )


def show_case(row: dict) -> dict:
    return public_case_with_state(
        parse_stored_case(row),
        case_id=str(row["id"]),
        image_url=background_url(
            row.get("image_path")
            or "fallback/classroom.svg"
        ),
        state=row.get("play_state") or {},
        manifest=row.get("media_manifest") or {},
    )


# ==================================================
# PROMPT CLOUDFLARE
# ==================================================


def build_background_prompt(
    case: DetectiveCase,
    age: int,
) -> str:
    """
    Tạo prompt ảnh nền hiện trường theo phong cách
    ảnh chụp chân thực thay vì hoạt hình.

    Các vật thể tương tác được FE vẽ riêng,
    vì vậy không để AI vẽ trùng lên ảnh nền.
    """
    scenes = {
        "classroom": "a real Vietnamese primary school classroom",
        "garden": "a real school garden with healthy plants",
        "lab": "a real bright and safe elementary science room",
    }

    interactive_assets = ", ".join(
        sorted({
            obj.asset_id.replace("_", " ")
            for obj in case.objects
        })
    )

    prompt = (
        "Photorealistic documentary-style environmental photograph, "
        "natural daylight, lifelike materials, believable real-world "
        "textures, realistic proportions, detailed but calm scene, "
        "soft natural colors, high-resolution photography. "
        f"Location: {scenes[case.scene_id]}. "
        f"Suitable and welcoming for a child aged {age}. "
        f"Scene details: {case.background_prompt}. "
        "Leave some visually clear open space for clickable objects "
        "that will be layered on top by the web application. "
        "No cartoon, no anime, no vector art, no painting, "
        "no 3D rendering, no exaggerated fantasy elements. "
        "No text, labels, logos, or visible people. "
        "Do not depict key interactive objects: "
        f"{interactive_assets}."
    )

    return prompt[:2048]


def build_clue_image_prompt(
    case: DetectiveCase,
    clue,
    age: int,
) -> str:
    """
    Sinh ảnh cận cảnh manh mối như ảnh chụp vật thật.

    Giữ nguyên visual_spec để hình ảnh phải thể hiện
    đúng dấu vết, không được tự tiết lộ lời giải.
    """
    spec = clue.visual_spec
    assert spec is not None

    brief = {
        "location": case.scene_id,
        "object_to_photograph": spec.subject,
        "observable_details": spec.must_show,
        "must_not_appear": spec.must_not_show + [
            "culprit", "answer", "labels", "text",
            "numbers", "logos", "people",
        ],
        "style": "photorealistic scientific macro photography",
    }

    return (
        "A high-resolution, realistic macro photograph of a real "
        f"physical object for a science detective game, age {age}. "
        "Natural light, true-to-life colors and textures, sharp "
        "focus on visible scientific evidence and a soft background. "
        "Show only the observed object and its observable marks. "
        "Do not guess or reveal the culprit, cause, or answer. "
        "No cartoon, drawing, illustration, 3D render, fake labels, "
        "arrows or text. "
        + json.dumps(brief, ensure_ascii=False)
    )[:2048]


async def generate_clue_images(
    case: DetectiveCase,
    child_id: int,
    age: int,
    case_id: str,
) -> dict:
    max_extra = min(
        2,
        max(
            0,
            get_settings().DETECTIVE_MAX_EXTRA_IMAGES,
        ),
    )

    priority = list(
        case.solution.required_evidence_ids
    )

    ordered_ids = priority + [
        c.id
        for c in case.clues
        if c.id not in priority
    ]

    manifest: dict = {
        "clue_images": {},
    }

    for clue_id in ordered_ids:
        if len(
            manifest["clue_images"]
        ) >= max_extra:
            break

        clue = next(
            (
                c
                for c in case.clues
                if c.id == clue_id
            ),
            None,
        )

        if clue is None or clue.visual_spec is None:
            continue

        try:
            image, mime = await call_image_generation(
                prompt=build_clue_image_prompt(
                    case,
                    clue,
                    age,
                )
            )

            path = await upload_clue_image(
                image,
                mime,
                child_id=child_id,
                case_id=case_id,
                clue_id=clue.id,
            )

            manifest["clue_images"][clue.id] = path

        except (
            LLMClientError,
            DetectiveStorageError,
        ) as exc:
            logger.warning(
                "Ảnh clue %s thất bại: %s",
                clue.id,
                type(exc).__name__,
            )

    return manifest


# ==================================================
# ẢNH DỰ PHÒNG
# ==================================================

@router.get(
    "/backgrounds/{scene_id}.svg",
    include_in_schema=False,
)
async def fallback_background(
    scene_id: Literal[
        "classroom",
        "garden",
        "lab",
    ]
):
    return FileResponse(
        STATIC_DIR / f"{scene_id}.svg",
        media_type="image/svg+xml",
    )


# ==================================================
# SINH VỤ ÁN
# ==================================================

@router.post(
    "/generate",
    status_code=200,
    response_model=GenerateCaseResponse,
)
async def generate_case(
    body: GenerateCaseRequest,
    db: AsyncClient = Depends(get_supabase),
):
    if (
        body.topic_id not in TOPIC_NAMES
        and body.topic_id != "random"
    ):
        return error(
            422,
            "INVALID_TOPIC",
            "Chủ đề không hợp lệ.",
        )

    # 1. Lấy tuổi/sở thích từ Supabase.
    try:
        profile_result = await (
            db.table("child_profiles")
            .select("id, age, interests")
            .eq("id", body.child_id)
            .limit(1)
            .execute()
        )

    except APIError:
        logger.exception("Không đọc được hồ sơ")
        return database_error()

    if not profile_result.data:
        return error(
            404,
            "CHILD_NOT_FOUND",
            "Không tìm thấy hồ sơ của bé.",
        )

    profile = profile_result.data[0]

    age = profile.get("age")

    if (
        not isinstance(age, int)
        or not 3 <= age <= 15
    ):
        return error(
            422,
            "INVALID_CHILD_AGE",
            "Tuổi trong hồ sơ không hợp lệ.",
        )

    interests = profile.get("interests")

    interests = (
        [
            s for s in interests
            if isinstance(s, str)
        ]
        if isinstance(interests, list)
        else []
    )

    # 2. Lấy 5 vụ án mới tạo gần nhất.
    try:
        recent = await (
            db.table("detective_cases")
            .select("topic_id, title, case_data")
            .eq("child_id", body.child_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

    except APIError:
        logger.exception("Không lấy được lịch sử")
        return database_error()

    # 3. Gemini sinh kịch bản.
    try:
        case = await generate_detective_case(
            topic_id=body.topic_id,
            age=age,
            interests=interests,
            recent_cases=recent.data or [],
            max_attempts=3,
            require_visuals=True,
        )

    except InvalidCaseOutputError:
        return error(
            502,
            "INVALID_CASE_OUTPUT",
            "AI chưa tạo được vụ án hợp lệ.",
        )

    except LLMTimeoutError:
        return error(
            504,
            "DETECTIVE_TIMEOUT",
            "Tạo vụ án mất nhiều thời gian.",
        )

    except (
        LLMUnavailableError,
        LLMClientError,
    ):
        return error(
            503,
            "DETECTIVE_GENERATION_FAILED",
            "AI đang bận. Con hãy thử lại nhé!",
        )

    new_case_id = str(uuid4())

    # 4. Cloudflare tạo ảnh nền.
    image_path = f"fallback/{case.scene_id}.svg"

    try:
        image, mime = await call_image_generation(
            prompt=build_background_prompt(
                case, age
            )
        )

        image_path = await upload_background(
            image,
            mime,
            child_id=body.child_id,
            case_id=new_case_id,
        )

    except (
        LLMClientError,
        DetectiveStorageError,
    ) as exc:
        logger.warning(
            "Ảnh nền thất bại: %s",
            type(exc).__name__,
        )

    # 5. Tạo tối đa hai ảnh clue.
    manifest = await generate_clue_images(
        case,
        body.child_id,
        age,
        new_case_id,
    )

    # 6. Lưu DB.
    try:
        inserted = await (
            db.table("detective_cases")
            .insert({
                "id": new_case_id,
                "child_id": body.child_id,
                "topic_id": case.topic_id,
                "title": case.title,
                "case_data":
                    case.model_dump(mode="json"),
                "image_path": image_path,
                "media_manifest": manifest,
                "play_state": initial_play_state(),
            })
            .select("id")
            .execute()
        )

        if not inserted.data:
            raise ValueError(
                "Supabase không trả case_id"
            )

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Lưu vụ án thất bại")

        await remove_case_media(
            image_path,
            manifest,
        )

        return database_error()

    public = public_case_with_state(
        case,
        case_id=str(inserted.data[0]["id"]),
        image_url=background_url(image_path),
        state=initial_play_state(),
        manifest=manifest,
    )

    return ok(
        "Vụ án mới đã sẵn sàng!",
        public,
    )


# ==================================================
# LỊCH SỬ
# ==================================================

@router.get("/history")
async def history(
    child_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase),
):
    try:
        child = await (
            db.table("child_profiles")
            .select("id")
            .eq("id", child_id)
            .limit(1)
            .execute()
        )

        if not child.data:
            return error(
                404,
                "CHILD_NOT_FOUND",
                "Không tìm thấy hồ sơ của bé.",
            )

        rows = (
            await completed_rows(db, child_id)
        )[:5]

    except APIError:
        return database_error()

    return ok(
        "Lấy danh sách vụ án cũ thành công",
        {
            "cases": [
                {
                    "case_id": str(r["id"]),
                    "title": r["title"],
                    "topic_id": r["topic_id"],
                    "last_completed_at":
                        r["last_completed_at"],
                    "outcome":
                        r.get("last_outcome") or "solved",
                }
                for r in rows
            ]
        },
    )


# ==================================================
# TẢI VỤ ÁN
# ==================================================

@router.get(
    "/{case_id}",
    response_model=GenerateCaseResponse,
)
async def get_case(
    case_id: UUID,
    child_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load_case(
            db, case_id, child_id
        )

        if not row:
            return error(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        return ok(
            "Đã tải hiện trường vụ án",
            show_case(row),
        )

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Tải vụ án thất bại")
        return database_error()


# ==================================================
# CHƠI LẠI — KHÔNG GỌI AI
# ==================================================

@router.post(
    "/{case_id}/replay",
    response_model=GenerateCaseResponse,
)
async def replay(
    case_id: UUID,
    body: ChildRequest,
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load_case(
            db,
            case_id,
            body.child_id,
        )

        if not row:
            return error(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if row.get("last_completed_at") is None:
            return error(
                422,
                "INVALID_ACTION",
                "Chỉ chơi lại vụ án đã hoàn thành.",
            )

        new_state = initial_play_state()

        await persist_state(
            db,
            case_id,
            new_state,
        )

        row["play_state"] = new_state

        return ok(
            "Con có thể điều tra lại vụ án này!",
            show_case(row),
        )

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Replay thất bại")
        return database_error()


# ==================================================
# KHÁM PHÁ VẬT THỂ
# ==================================================

@router.post("/{case_id}/inspect")
async def inspect(
    case_id: UUID,
    body: InspectRequest,
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load_case(
            db,
            case_id,
            body.child_id,
        )

        if not row:
            return error(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if normalize_state(
            row.get("play_state")
        )["completed"]:
            return error(
                422,
                "INVALID_ACTION",
                "Con hãy chơi lại để tiếp tục khám phá.",
            )

        state, data = inspect_object(
            parse_stored_case(row),
            row.get("play_state"),
            body.object_id,
            row.get("media_manifest"),
        )

        await persist_state(
            db,
            case_id,
            state,
        )

        return ok(
            "Con đã tìm thấy manh mối!",
            data,
        )

    except InvalidActionError as exc:
        return invalid_action(exc)

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Inspect thất bại")
        return database_error()


# ==================================================
# THỬ NGHIỆM
# ==================================================

@router.post("/{case_id}/experiment")
async def experiment(
    case_id: UUID,
    body: ExperimentRequest,
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load_case(
            db, case_id, body.child_id
        )

        if not row:
            return error(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if normalize_state(
            row.get("play_state")
        )["completed"]:
            return error(
                422,
                "INVALID_ACTION",
                "Con hãy chơi lại để thử nghiệm lại.",
            )

        state, data = run_experiment(
            parse_stored_case(row),
            row.get("play_state"),
            body.experiment_id,
            row.get("media_manifest"),
        )

        await persist_state(
            db,
            case_id,
            state,
        )

        return ok(
            "Thử nghiệm hoàn tất",
            data,
        )

    except InvalidActionError as exc:
        return invalid_action(exc)

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Experiment thất bại")
        return database_error()


# ==================================================
# KẾT LUẬN TỐI ĐA HAI LƯỢT
# ==================================================

@router.post("/{case_id}/solve")
async def solve(
    case_id: UUID,
    body: SolveRequest,
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load_case(
            db,
            case_id,
            body.child_id,
        )

        if not row:
            return error(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        case = parse_stored_case(row)

        current = normalize_state(
            row.get("play_state")
        )

        # Vụ án đã kết thúc.
        if current["completed"]:
            rows = await completed_rows(
                db,
                body.child_id,
            )

            data = final_result(
                case,
                current,
            )

            data["history_count"] = min(
                len(rows),
                5,
            )

            return ok(
                "Vụ án đã khép lại!",
                data,
            )

        state, data = solve_case(
            case,
            current,
            body.hypothesis_id,
            body.evidence_ids,
            body.submission_id,
        )

        # Request trùng không tiêu hao lượt.
        if state == current:
            return ok(
                "Đây là kết luận con vừa gửi.",
                data,
            )

        # Cập nhật nguyên tử bằng SQL RPC.
        cas = await db.rpc(
            "detective_solve_compare_set",
            {
                "p_case_id": str(case_id),
                "p_child_id": body.child_id,
                "p_expected":
                    row.get("play_state") or {},
                "p_new": state,
                "p_finished": data["completed"],
                "p_outcome": data["outcome"],
            },
        ).execute()

        if cas.data is not True:
            fresh = await load_case(
                db,
                case_id,
                body.child_id,
            )

            if not fresh:
                return error(
                    404,
                    "CASE_NOT_FOUND",
                    "Không tìm thấy vụ án.",
                )

            fresh_state = normalize_state(
                fresh.get("play_state")
            )

            if fresh_state["completed"]:
                result = final_result(
                    case,
                    fresh_state,
                )

                rows = await completed_rows(
                    db,
                    body.child_id,
                )

                result["history_count"] = min(
                    len(rows),
                    5,
                )

                return ok(
                    "Vụ án đã khép lại!",
                    result,
                )

            repeated_state, repeated_data = solve_case(
                case,
                fresh_state,
                body.hypothesis_id,
                body.evidence_ids,
                body.submission_id,
            )

            if repeated_state == fresh_state:
                return ok(
                    "Đây là kết luận con vừa gửi.",
                    repeated_data,
                )

            return error(
                409,
                "CASE_STATE_CHANGED",
                "Vụ án vừa được cập nhật. "
                "Con hãy tải lại nhé!",
            )

        if data["completed"]:
            data["history_count"] = await trim_history(
                db,
                body.child_id,
            )

            return ok(
                "Vụ án đã khép lại!",
                data,
            )

        return ok(
            "Con còn một cơ hội nữa!",
            data,
        )

    except InvalidActionError as exc:
        return invalid_action(exc)

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Solve thất bại")
        return database_error()


# ==================================================
# GEMINI TTS
# ==================================================

@router.post("/{case_id}/narration")
async def narration(
    case_id: UUID,
    body: NarrationRequest,
    db: AsyncClient = Depends(get_supabase),
):
    if not get_settings().DETECTIVE_TTS_ENABLED:
        return error(
            503,
            "TTS_DISABLED",
            "Giọng cô giáo hiện chưa khả dụng.",
        )

    try:
        async with narration_lock(str(case_id)):
            row = await load_case(
                db,
                case_id,
                body.child_id,
            )

            if not row:
                return error(
                    404,
                    "CASE_NOT_FOUND",
                    "Không tìm thấy vụ án của bé.",
                )

            # BE tự chọn nội dung được phép đọc.
            text = narration_text(
                parse_stored_case(row),
                row.get("play_state") or {},
                body.segment_type,
                body.segment_id,
            )

            cache_version = (
                get_settings()
                .DETECTIVE_TTS_CACHE_VERSION
            )

            key = audio_cache_key(
                body.segment_type,
                body.segment_id,
                f"teacher_vi_{cache_version}",
                text,
            )

            manifest = (
                row.get("media_manifest") or {}
            )

            audio_map = (
                manifest.get("audio") or {}
            )

            path = audio_map.get(key)

            # Đã cache => không gọi Gemini.
            if isinstance(path, str) and path:
                return ok(
                    "Đã chuẩn bị giọng kể",
                    {
                        "audio_url":
                            public_image_url(path),
                        "mime_type": "audio/wav",
                        "cached": True,
                    },
                )

            wav = await call_speech_generation(text)

            path = await upload_audio(
                wav,
                child_id=body.child_id,
                case_id=str(case_id),
                cache_key=key,
            )

            persisted = await db.rpc(
                "detective_cache_audio_path",
                {
                    "p_case_id": str(case_id),
                    "p_child_id": body.child_id,
                    "p_cache_key": key,
                    "p_storage_path": path,
                },
            ).execute()

            if persisted.data != path:
                return database_error()

            return ok(
                "Đã chuẩn bị giọng kể",
                {
                    "audio_url":
                        public_image_url(path),
                    "mime_type": "audio/wav",
                    "cached": False,
                },
            )

    except InvalidActionError as exc:
        return invalid_action(exc)

    except (
        LLMClientError,
        DetectiveStorageError,
    ) as exc:
        logger.warning(
            "Gemini TTS lỗi: %s",
            type(exc).__name__,
        )

        return error(
            503,
            "TTS_UNAVAILABLE",
            "Chưa phát được giọng cô giáo, "
            "con vẫn đọc được nội dung nhé.",
        )

    except (
        APIError,
        ValueError,
    ):
        logger.exception("Narration thất bại")
        return database_error()

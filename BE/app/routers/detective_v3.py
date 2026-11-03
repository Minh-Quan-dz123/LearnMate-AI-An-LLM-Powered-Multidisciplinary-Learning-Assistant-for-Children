
"""
LEARNMATE AI — DETECTIVE ROUTER V3.

Đăng ký router này TRƯỚC detective.router V2.

Các endpoint:
POST /api/detective/generate
GET  /api/detective/history
GET  /api/detective/{case_id}
POST /api/detective/{case_id}/hint
POST /api/detective/{case_id}/solve
POST /api/detective/{case_id}/replay

V2:
- inspect
- experiment
- narration
- solve
- replay

Được chuyển tiếp sang router V2 cũ.
"""

from __future__ import annotations

import asyncio
import logging
import httpx

from app.config import get_settings

from app.llm_client import call_speech_generation

from app.services.detective_storage import (
    upload_audio,
    public_image_url,
)

from app.services.detective_narration import (
    narration_lock,
    audio_cache_key,
)

from app.services.detective_narration_v3 import (
    narration_text_v3,
)

from app.services.detective_engine import (
    InvalidActionError,
)

from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from postgrest.exceptions import APIError
from pydantic import ValidationError
from supabase import AsyncClient

from app.database import get_supabase

from app.llm_client import (
    call_image_generation,
    LLMClientError,
    LLMTimeoutError,
    LLMUnavailableError,
)

from app.routers import detective as v2

from app.schemas.detective import (
    TOPIC_NAMES,
)

from app.schemas.detective_v3 import (
    ChildRequestV3,
    GenerateRequestV3,
    HintRequest,
    SolveRequestV3,
    DetectiveCaseV3,
)

from app.services.detective_storage import (
    DetectiveStorageError,
    upload_background,
    remove_case_media,
)

from app.services.detective_v3 import (
    SceneMismatch,
    initial_state,
    normalize_state,
    public_case,
    public_hint,
    generate_draft,
    canonical_image_prompt,
    localize_hints,
    evaluate_open,
    choice_assessment,
    build_solve_result,
)


router = APIRouter(
    prefix="/api/detective",
    tags=["Detective V3"],
)

logger = logging.getLogger(__name__)

# Chống hai kết luận đồng thời trong một process.
# CAS trong PostgreSQL vẫn là nguồn chân lý.
_solve_locks: dict[str, asyncio.Lock] = {}


# ============================================================
# 1. HELPERS
# ============================================================

def fail(
    status: int,
    code: str,
    message: str,
):
    return v2.error(
        status,
        code,
        message,
    )


def parse_body(model, body: dict):
    try:
        return model.model_validate(body)
    except (
        ValidationError,
        ValueError,
    ):
        return None


def is_v3(row: dict) -> bool:
    data = row.get("case_data") or {}

    return (
        isinstance(data, dict)
        and data.get("schema_version") == 3
    )


async def load(
    db: AsyncClient,
    case_id: UUID,
    child_id: int,
):
    return await v2.load_case(
        db,
        case_id,
        child_id,
    )


# ============================================================
# 2. GENERATE NEW CASE V3
# ============================================================

@router.post("/generate")
async def generate_v3(
    body: GenerateRequestV3,
    db: AsyncClient = Depends(get_supabase),
):
    """
    Tạo vụ án mới.

    Một lần tạo thành công:
    1 Gemini Text
    1 Cloudflare Image
    1 Gemini Vision
    1 ảnh lưu Storage

    Không sinh clue image bổ sung.
    """

    if (
        body.topic_id != "random"
        and body.topic_id not in TOPIC_NAMES
    ):
        return fail(
            422,
            "INVALID_TOPIC",
            "Chủ đề không hợp lệ.",
        )

    # --------------------------------------------------------
    # 2.1. Lấy hồ sơ bé và lịch sử
    # --------------------------------------------------------

    try:
        found = await (
            db.table("child_profiles")
            .select("age,interests")
            .eq("id", body.child_id)
            .limit(1)
            .execute()
        )

        if not found.data:
            return fail(
                404,
                "CHILD_NOT_FOUND",
                "Không tìm thấy hồ sơ của bé.",
            )

        profile = found.data[0]

        age = profile.get("age")

        if (
            type(age) is not int
            or not 3 <= age <= 15
        ):
            return fail(
                422,
                "INVALID_CHILD_AGE",
                "Tuổi của bé không hợp lệ.",
            )

        interests = (
            profile.get("interests") or []
        )

        recent = await (
            db.table("detective_cases")
            .select("title,topic_id")
            .eq("child_id", body.child_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

    except APIError:
        logger.exception(
            "Không đọc được hồ sơ/lịch sử V3"
        )
        return v2.database_error()

    # --------------------------------------------------------
    # 2.2. GEMINI TEXT -> CLOUDFLARE -> VISION
    # --------------------------------------------------------

    try:
        
        # ====================================================
        # TỰ ĐỘNG TẠO LẠI NẾU ẢNH THIẾU DẤU VẾT
        #
        # Quy trình mỗi lần:
        # 1. Gemini Text sinh kịch bản.
        # 2. Cloudflare sinh một ảnh mới.
        # 3. Gemini Vision kiểm tra các dấu vết.
        #
        # Nếu không tìm thấy đủ dấu vết:
        #   -> Bỏ ứng viên hiện tại.
        #   -> Sinh ứng viên mới, tối đa 2 lần.
        #
        # Chỉ lưu một ứng viên đã vượt qua Vision.
        # ====================================================

        MAX_SCENE_ATTEMPTS = 2

        for attempt in range(
            1,
            MAX_SCENE_ATTEMPTS + 1
        ):

            # 1. Sinh kịch bản mới.
            draft = await generate_draft(
                body.topic_id,
                age,
                interests,
                recent.data or [],
            )

            # 2. Sinh một ảnh cho kịch bản này.
            image, mime = await call_image_generation(
                canonical_image_prompt(
                    draft,
                    age,
                )
            )

            # 3. Kiểm tra ảnh bằng Gemini Vision.
            try:
                case = await localize_hints(
                    image,
                    mime,
                    draft,
                )

                # Đủ tất cả manh mối:
                # kết thúc vòng lặp.
                break

            except (
                SceneMismatch,
                ValidationError,
            ) as exc:

                logger.warning(
                    "Ứng viên V3 %s/%s không đạt: %s",
                    attempt,
                    MAX_SCENE_ATTEMPTS,
                    str(exc)[:250],
                )

                # Đã thử hết số lần cho phép.
                # Chuyển lỗi sang except ngoài,
                # trả SCENE_EVIDENCE_MISMATCH.
                if attempt == MAX_SCENE_ATTEMPTS:
                    raise


    except LLMTimeoutError:
        return fail(
            504,
            "LLM_TIMEOUT",
            "AI phản hồi quá chậm. "
            "Con hãy thử tạo lại nhé!",
        )

    except (
        LLMUnavailableError,
        LLMClientError,
    ):
        return fail(
            503,
            "LLM_UNAVAILABLE",
            "AI đang bận. "
            "Con hãy thử lại sau nhé!",
        )

    except (
        SceneMismatch,
        ValidationError,
    ) as exc:
        logger.warning(
            "Vision V3 không đạt: %s",
            str(exc)[:150],
        )

        return fail(
            502,
            "SCENE_EVIDENCE_MISMATCH",
            "Ảnh chưa thể hiện đủ dấu vết. "
            "Con hãy tạo vụ án khác nhé!",
        )

    except (
        ValueError,
        TypeError,
    ) as exc:
        logger.warning(
            "Kịch bản V3 không đạt: %s",
            type(exc).__name__,
        )

        return fail(
            502,
            "INVALID_MODEL_OUTPUT",
            "AI chưa tạo được vụ án hợp lệ. "
            "Con hãy thử lại nhé!",
        )

    # --------------------------------------------------------
    # 2.3. Lưu một ảnh và vụ án vào Supabase
    # --------------------------------------------------------

    
    # --------------------------------------------------------
    # 2.3. Lưu ảnh và vụ án vào Supabase
    # --------------------------------------------------------

    case_id = str(uuid4())
    image_path = None

    try:
        # 1. Upload ảnh lên Supabase Storage.
        image_path = await upload_background(
            image,
            mime,
            child_id=body.child_id,
            case_id=case_id,
        )

        state = initial_state()

        # 2. Ghi thông tin vụ án vào Database.
        #
        # Nếu kết nối Supabase lỗi tạm thời,
        # thử lại tối đa 3 lần.
        #
        # Chỉ retry lỗi không thiết lập được kết nối,
        # không retry lỗi SQL hoặc dữ liệu không hợp lệ.
        #
        # Giữ nguyên case_id, image_path và case_data,
        # không gọi lại Gemini hoặc Cloudflare.

        for attempt in range(3):
            try:
                inserted = await (
                    db.table("detective_cases")
                    .insert({
                        "id": case_id,
                        "child_id": body.child_id,
                        "topic_id": case.topic_id,
                        "title": case.title,

                        "case_data":
                            case.model_dump(mode="json"),

                        "image_path": image_path,

                        "media_manifest": {},

                        "play_state": state,
                    })
                    .select("id")
                    .execute()
                )

                # Lưu thành công.
                break

            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
            ) as exc:

                logger.warning(
                    "Không kết nối được Supabase "
                    "khi lưu vụ án (lần %s/3): %s",
                    attempt + 1,
                    type(exc).__name__,
                )

                # Đã thử đủ 3 lần.
                if attempt == 2:
                    raise

                # Chờ một chút rồi thử lại.
                await asyncio.sleep(
                    0.7 * (2 ** attempt)
                )

        if not inserted.data:
            raise RuntimeError(
                "Insert vụ án không trả ID"
            )

    except (
        httpx.ReadError,
        httpx.ReadTimeout,
    ):
        # Mất kết nối khi đang chờ phản hồi.
        #
        # Không chắc chắn Supabase đã ghi DB
        # hay chưa, vì vậy không tự xóa ảnh:
        # có thể làm hỏng vụ án đã được lưu.
        logger.exception(
            "Mất kết nối khi chờ Supabase "
            "trả kết quả INSERT"
        )

        return v2.database_error()

    except (
        APIError,
        httpx.RequestError,
        DetectiveStorageError,
        RuntimeError,
    ):
        logger.exception(
            "Không lưu được vụ án V3"
        )

        # Trường hợp kết nối thất bại trước
        # khi ghi DB, dọn ảnh đã upload.
        if image_path:
            await remove_case_media(
                image_path,
                {},
            )

        # Trả về lỗi có kiểm soát,
        # không để FastAPI phát sinh HTTP 500.
        return v2.database_error()

    # --------------------------------------------------------
    # 2.4. Public response
    # --------------------------------------------------------

    data = public_case({
        "id": case_id,
        "case_data":
            case.model_dump(mode="json"),
        "image_path": image_path,
        "play_state": state,
    })

    return v2.ok(
        "Vụ án mới đã sẵn sàng!",
        data,
    )


# ============================================================
# 3. HISTORY — DÙNG CHUNG V2/V3
# ============================================================

@router.get("/history")
async def history_compat(
    child_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase),
):
    """
    Trả tối đa 5 vụ án đã kết thúc.

    Gồm cả:
    - V2
    - V3
    - solved
    - unsolved
    """

    return await v2.history(
        child_id,
        db,
    )


# ============================================================
# 4. GET CASE — TỰ PHÂN BIỆT VERSION
# ============================================================

@router.get("/{case_id}")
async def read_case_v3(
    case_id: UUID,
    child_id: int = Query(gt=0),
    db: AsyncClient = Depends(get_supabase),
):
    try:
        row = await load(
            db,
            case_id,
            child_id,
        )

        if not row:
            return fail(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if is_v3(row):
            data = public_case(row)
        else:
            data = v2.show_case(row)

        return v2.ok(
            "Đã tải hiện trường vụ án",
            data,
        )

    except (
        APIError,
        ValueError,
        ValidationError,
        DetectiveStorageError,
    ):
        logger.exception(
            "GET vụ án thất bại"
        )
        return v2.database_error()


# ============================================================
# 5. REVEAL HINT — V3
# ============================================================

@router.post("/{case_id}/hint")
async def reveal_hint_v3(
    case_id: UUID,
    body: HintRequest,
    db: AsyncClient = Depends(get_supabase),
):
    """
    Mở gợi ý tiếp theo.

    Gọi RPC PostgreSQL để:
    - Khóa hàng.
    - Chống double-click.
    - Idempotent theo request_id.
    - Không mở hai hint cùng lúc do race.

    Không gọi Gemini hoặc Cloudflare.
    """

    try:
        result = await db.rpc(
            "detective_reveal_next_hint",
            {
                "p_case_id": str(case_id),
                "p_child_id": body.child_id,
                "p_request_id":
                    str(body.request_id),
            },
        ).execute()

        data = result.data

        if not isinstance(data, dict):
            return v2.database_error()

        if data.get("error"):
            code = data["error"]

            mapping = {
                "CASE_NOT_FOUND": (
                    404,
                    "Không tìm thấy vụ án.",
                ),

                "CASE_VERSION_UNSUPPORTED": (
                    422,
                    "Vụ án cũ không hỗ trợ gợi ý V3.",
                ),

                "CASE_ALREADY_COMPLETED": (
                    409,
                    "Vụ án đã kết thúc.",
                ),

                "HINTS_EXHAUSTED": (
                    409,
                    "Con đã dùng hết gợi ý.",
                ),
            }

            status, message = mapping.get(
                code,
                (
                    422,
                    "Yêu cầu gợi ý không hợp lệ.",
                ),
            )

            return fail(
                status,
                code,
                message,
            )

        # Chỉ truy vấn hint vừa được RPC mở.
        row = await load(
            db,
            case_id,
            body.child_id,
        )

        if not row or not is_v3(row):
            return fail(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án.",
            )

        case = DetectiveCaseV3.model_validate(
            row["case_data"]
        )

        hint = next(
            (
                item
                for item in case.hints
                if item.id == data["hint_id"]
            ),
            None,
        )

        if hint is None:
            return v2.database_error()

        ids = data["revealed_hint_ids"]

        return v2.ok(
            "Con đã khám phá thêm một gợi ý!",
            {
                "hint": public_hint(hint),

                "revealed_hint_ids": ids,

                "hints_used": len(ids),

                "hint_count": len(case.hints),

                "remaining_hints":
                    len(case.hints) - len(ids),

                "already_revealed_for_request":
                    bool(
                        data[
                            "already_revealed_for_request"
                        ]
                    ),
            },
        )

    except (
        APIError,
        ValueError,
        ValidationError,
        KeyError,
    ):
        logger.exception(
            "Lỗi mở gợi ý V3"
        )

        return v2.database_error()


# ============================================================
# 6. REPLAY — V2/V3
# ============================================================

@router.post("/{case_id}/replay")
async def replay_v3(
    case_id: UUID,
    body: ChildRequestV3,
    db: AsyncClient = Depends(get_supabase),
):
    """
    Replay V3:
    - Reset state.
    - Giữ ảnh.
    - Giữ kịch bản.
    - Không gọi AI.

    Replay V2:
    - Chuyển sang router cũ.
    """

    try:
        row = await load(
            db,
            case_id,
            body.child_id,
        )

        if not row:
            return fail(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if not is_v3(row):
            return await v2.replay(
                case_id,
                v2.ChildRequest(
                    child_id=body.child_id
                ),
                db,
            )

        fresh_state = initial_state()

        result = await db.rpc(
            "detective_replay_v3",
            {
                "p_case_id": str(case_id),
                "p_child_id": body.child_id,
                "p_initial": fresh_state,
            },
        ).execute()

        if result.data is not True:
            return fail(
                409,
                "CASE_STATE_CHANGED",
                "Chỉ có thể chơi lại vụ án "
                "đã kết thúc.",
            )

        row["play_state"] = fresh_state

        return v2.ok(
            "Con có thể điều tra lại vụ án này!",
            public_case(row),
        )

    except (
        APIError,
        ValidationError,
        ValueError,
    ):
        logger.exception(
            "Replay V3 thất bại"
        )
        return v2.database_error()


# ============================================================
# 7. SOLVE — CHOICE / OPEN
# ============================================================

@router.post("/{case_id}/solve")
async def solve_v3(
    case_id: UUID,
    body: dict,
    db: AsyncClient = Depends(get_supabase),
):
    """
    V3:
    - Choice: so ID.
    - Open: Gemini chấm theo nghĩa.
    - Tối đa 2 lượt.
    - Idempotent theo submission_id.
    - CAS lưu DB.

    V2:
    - Sử dụng hàm solve cũ.
    """

    child_id = (
        body.get("child_id")
        if isinstance(body, dict)
        else None
    )

    if (
        type(child_id) is not int
        or child_id <= 0
    ):
        return fail(
            422,
            "INVALID_INPUT",
            "Hồ sơ bé không hợp lệ.",
        )

    # --------------------------------------------------------
    # 7.1. Phân biệt version
    # --------------------------------------------------------

    try:
        row = await load(
            db,
            case_id,
            child_id,
        )

        if not row:
            return fail(
                404,
                "CASE_NOT_FOUND",
                "Không tìm thấy vụ án của bé.",
            )

        if not is_v3(row):
            parsed_v2 = parse_body(
                v2.SolveRequest,
                body,
            )

            if parsed_v2 is None:
                return fail(
                    422,
                    "INVALID_INPUT",
                    "Kết luận V2 không hợp lệ.",
                )

            return await v2.solve(
                case_id,
                parsed_v2,
                db,
            )

    except APIError:
        return v2.database_error()

    # --------------------------------------------------------
    # 7.2. Validate request V3
    # --------------------------------------------------------

    parsed = parse_body(
        SolveRequestV3,
        body,
    )

    if parsed is None:
        return fail(
            422,
            "INVALID_OPEN_ANSWER",
            "Con hãy chọn hoặc viết kết luận "
            "hợp lệ, tối đa 1000 ký tự.",
        )

    lock = _solve_locks.setdefault(
        str(case_id),
        asyncio.Lock(),
    )

    async with lock:
        try:
            # ------------------------------------------------
            # 7.3. Đọc lại state sau khi lấy khóa
            # ------------------------------------------------

            row = await load(
                db,
                case_id,
                parsed.child_id,
            )

            if not row or not is_v3(row):
                return fail(
                    404,
                    "CASE_NOT_FOUND",
                    "Không tìm thấy vụ án.",
                )

            case = DetectiveCaseV3.model_validate(
                row["case_data"]
            )

            old_raw = (
                row.get("play_state") or {}
            )

            state = normalize_state(
                old_raw
            )

            request_key = str(
                parsed.submission_id
            )

            # ------------------------------------------------
            # 7.4. Retry cùng submission_id
            # ------------------------------------------------

            cached = state[
                "submission_results"
            ].get(request_key)

            if cached is not None:
                return v2.ok(
                    "Đây là kết luận con vừa gửi.",
                    cached,
                )

            if (
                state["last_submission_id"]
                == request_key
                and state["last_submission_result"]
            ):
                return v2.ok(
                    "Đây là kết luận con vừa gửi.",
                    state["last_submission_result"],
                )

            # ------------------------------------------------
            # 7.5. Kiểm tra số lượt
            # ------------------------------------------------

            if state["completed"]:
                return v2.ok(
                    "Vụ án đã khép lại!",
                    state["last_submission_result"],
                )

            if state["attempts_used"] >= 2:
                return fail(
                    409,
                    "CASE_ALREADY_COMPLETED",
                    "Vụ án đã hết lượt kết luận.",
                )

            # ------------------------------------------------
            # 7.6. Chấm choice hoặc open
            # ------------------------------------------------

            if parsed.answer_mode == "choice":

                # Choice hoàn toàn không gọi AI.
                try:
                    assessment = choice_assessment(
                        case,
                        parsed.hypothesis_id,
                        state["revealed_hint_ids"],
                    )

                except ValueError:
                    return fail(
                        422,
                        "INVALID_INPUT",
                        "Giả thuyết con chọn không hợp lệ.",
                    )

            else:

                # Open dùng Gemini Text.
                # Chưa commit DB trước khi AI trả kết quả.

                child_result = await (
                    db.table("child_profiles")
                    .select("age")
                    .eq("id", parsed.child_id)
                    .limit(1)
                    .execute()
                )

                if not child_result.data:
                    return fail(
                        404,
                        "CHILD_NOT_FOUND",
                        "Không tìm thấy hồ sơ của bé.",
                    )

                assessment_obj = await evaluate_open(
                    case,
                    state["revealed_hint_ids"],
                    parsed.answer_text.strip(),
                    child_result.data[0]["age"],
                )

                assessment = (
                    assessment_obj.model_dump()
                )

            # ------------------------------------------------
            # 7.7. Xây kết quả mới
            # ------------------------------------------------

            data = build_solve_result(
                case,
                state,
                assessment,
            )

            new_submission_results = {
                **state["submission_results"],
                request_key: data,
            }

            next_state = {
                **state,

                "attempts_used":
                    data["attempts_used"],

                "completed":
                    data["completed"],

                "outcome":
                    data["outcome"],

                "last_submission_id":
                    request_key,

                "last_submission_result":
                    data,

                "submission_results":
                    new_submission_results,
            }

            # ------------------------------------------------
            # 7.8. CAS — cập nhật nguyên tử
            # ------------------------------------------------

            cas = await db.rpc(
                "detective_solve_compare_set",
                {
                    "p_case_id": str(case_id),

                    "p_child_id":
                        parsed.child_id,

                    "p_expected": old_raw,

                    "p_new": next_state,

                    "p_finished":
                        data["completed"],

                    "p_outcome":
                        data["outcome"],
                },
            ).execute()

            if cas.data is not True:

                # State đã thay đổi trong lúc Gemini chấm.
                fresh = await load(
                    db,
                    case_id,
                    parsed.child_id,
                )

                fresh_state = (
                    normalize_state(
                        fresh.get("play_state")
                    )
                    if fresh
                    else None
                )

                if fresh_state:
                    previous_result = (
                        fresh_state[
                            "submission_results"
                        ].get(request_key)
                    )

                    if previous_result is not None:
                        return v2.ok(
                            "Đây là kết luận con vừa gửi.",
                            previous_result,
                        )

                    if (
                        fresh_state[
                            "last_submission_id"
                        ] == request_key
                    ):
                        return v2.ok(
                            "Đây là kết luận con vừa gửi.",
                            fresh_state[
                                "last_submission_result"
                            ],
                        )

                return fail(
                    409,
                    "CASE_STATE_CHANGED",
                    "Vụ án vừa được cập nhật. "
                    "Con hãy tải lại trước khi nộp.",
                )

            # ------------------------------------------------
            # 7.9. Hoàn thành vụ án
            # ------------------------------------------------

            if data["completed"]:
                try:
                    data["history_count"] = (
                        await v2.trim_history(
                            db,
                            parsed.child_id,
                        )
                    )
                except Exception:
                    logger.exception(
                        "Đã lưu kết quả nhưng dọn "
                        "history thất bại"
                    )

                return v2.ok(
                    "Vụ án đã khép lại!",
                    data,
                )

            # Sai lượt 1, còn lượt 2.
            return v2.ok(
                "Con còn một cơ hội nữa!",
                data,
            )

        # ----------------------------------------------------
        # 7.10. Lỗi AI/DB
        # ----------------------------------------------------

        except LLMTimeoutError:
            return fail(
                504,
                "LLM_TIMEOUT",
                "AI phản hồi chậm. "
                "Con thử nộp lại nhé!",
            )

        except (
            LLMClientError,
            LLMUnavailableError,
        ):
            return fail(
                503,
                "LLM_UNAVAILABLE",
                "AI đang bận. "
                "Con thử nộp lại nhé!",
            )

        except (
            ValueError,
            ValidationError,
        ):
            return fail(
                502,
                "INVALID_MODEL_OUTPUT",
                "AI chưa chấm được kết luận. "
                "Con thử lại nhé!",
            )

        except APIError:
            logger.exception(
                "DB solve V3 thất bại"
            )
            return v2.database_error()


# ============================================================
# 8. V2 COMPATIBILITY — INSPECT
# ============================================================

@router.post("/{case_id}/inspect")
async def inspect_compat(
    case_id: UUID,
    body: dict,
    db: AsyncClient = Depends(get_supabase),
):
    parsed = parse_body(
        v2.InspectRequest,
        body,
    )

    if parsed is None:
        return fail(
            422,
            "INVALID_INPUT",
            "Vật thể không hợp lệ.",
        )

    row = await load(
        db,
        case_id,
        parsed.child_id,
    )

    if row and is_v3(row):
        return fail(
            422,
            "CASE_VERSION_UNSUPPORTED",
            "V3 sử dụng nút Dùng gợi ý.",
        )

    return await v2.inspect(
        case_id,
        parsed,
        db,
    )


# ============================================================
# 9. V2 COMPATIBILITY — EXPERIMENT
# ============================================================

@router.post("/{case_id}/experiment")
async def experiment_compat(
    case_id: UUID,
    body: dict,
    db: AsyncClient = Depends(get_supabase),
):
    parsed = parse_body(
        v2.ExperimentRequest,
        body,
    )

    if parsed is None:
        return fail(
            422,
            "INVALID_INPUT",
            "Thử nghiệm không hợp lệ.",
        )

    row = await load(
        db,
        case_id,
        parsed.child_id,
    )

    if row and is_v3(row):
        return fail(
            422,
            "CASE_VERSION_UNSUPPORTED",
            "V3 không có tab thử nghiệm.",
        )

    return await v2.experiment(
        case_id,
        parsed,
        db,
    )


# ============================================================
# 10. V2 COMPATIBILITY — NARRATION
# ============================================================


# ============================================================
# GEMINI TTS — MODULE 3 V2 + V3
#
# V3:
#   introduction       -> Giới thiệu vụ án
#   retry_feedback     -> Sai lượt đầu
#   final_explanation  -> Kết thúc vụ án
#
# V2:
#   Chuyển về narration() cũ.
#
# Giữ nguyên cơ chế:
#   LLM Server -> Gemini TTS -> Supabase Storage
# ============================================================

@router.post("/{case_id}/narration")
async def narration_compat(
    case_id: UUID,
    body: dict,
    db: AsyncClient = Depends(get_supabase),
):
    # --------------------------------------------------------
    # 1. Validate request
    # --------------------------------------------------------

    parsed = parse_body(
        v2.NarrationRequest,
        body,
    )

    if parsed is None:
        return fail(
            422,
            "INVALID_INPUT",
            "Yêu cầu giọng kể không hợp lệ.",
        )

    settings = get_settings()

    if not settings.DETECTIVE_TTS_ENABLED:
        return fail(
            503,
            "TTS_DISABLED",
            "Giọng cô giáo hiện chưa khả dụng.",
        )

    try:
        # ----------------------------------------------------
        # 2. Khóa theo case_id
        #
        # Tránh nhiều request trong cùng một process
        # đồng thời tạo cùng một file âm thanh.
        # ----------------------------------------------------

        async with narration_lock(str(case_id)):

            row = await load(
                db,
                case_id,
                parsed.child_id,
            )

            if not row:
                return fail(
                    404,
                    "CASE_NOT_FOUND",
                    "Không tìm thấy vụ án.",
                )

            # ------------------------------------------------
            # 3. Vụ án V2
            #
            # Để V2 xử lý bên ngoài lock.
            # V2 đã có cơ chế lock riêng.
            # ------------------------------------------------

            if not is_v3(row):
                pass

            else:
                # --------------------------------------------
                # 4. Vụ án V3
                # --------------------------------------------

                case = DetectiveCaseV3.model_validate(
                    row["case_data"]
                )

                # BE tự xác định văn bản được phép đọc.
                # Không nhận văn bản tùy ý từ FE.
                speech_text = narration_text_v3(
                    case,
                    row.get("play_state") or {},
                    parsed.segment_type,
                    parsed.segment_id,
                )

                # --------------------------------------------
                # 5. Tạo khóa cache theo nội dung
                # --------------------------------------------

                cache_version = (
                    settings.DETECTIVE_TTS_CACHE_VERSION
                )

                cache_key = audio_cache_key(
                    parsed.segment_type,
                    None,
                    f"v3_teacher_vi_{cache_version}",
                    speech_text,
                )

                manifest = (
                    row.get("media_manifest") or {}
                )

                audio_map = (
                    manifest.get("audio") or {}
                )

                existing_path = audio_map.get(
                    cache_key
                )

                # --------------------------------------------
                # 6. Nếu audio đã tồn tại:
                #    trả URL, không gọi Gemini.
                # --------------------------------------------

                if (
                    isinstance(existing_path, str)
                    and existing_path
                ):
                    return v2.ok(
                        "Giọng Gemini đã sẵn sàng.",
                        {
                            "audio_url":
                                public_image_url(
                                    existing_path
                                ),

                            "mime_type": "audio/wav",

                            "cached": True,
                        },
                    )

                # --------------------------------------------
                # 7. Chưa có cache:
                #    gọi Gemini TTS qua LLM Server.
                # --------------------------------------------

                wav = await call_speech_generation(
                    speech_text
                )

                # --------------------------------------------
                # 8. Upload WAV lên Supabase Storage
                # --------------------------------------------

                audio_path = await upload_audio(
                    wav,
                    child_id=parsed.child_id,
                    case_id=str(case_id),
                    cache_key=cache_key,
                )

                # --------------------------------------------
                # 9. Ghi đường dẫn vào media_manifest
                #    bằng RPC đang dùng trong V2.
                # --------------------------------------------

                saved = await db.rpc(
                    "detective_cache_audio_path",
                    {
                        "p_case_id": str(case_id),

                        "p_child_id": parsed.child_id,

                        "p_cache_key": cache_key,

                        "p_storage_path": audio_path,
                    },
                ).execute()

                if saved.data != audio_path:
                    return v2.database_error()

                # --------------------------------------------
                # 10. Trả URL audio vừa tạo
                # --------------------------------------------

                return v2.ok(
                    "Giọng Gemini đã sẵn sàng.",
                    {
                        "audio_url": public_image_url(
                            audio_path
                        ),

                        "mime_type": "audio/wav",

                        "cached": False,
                    },
                )

    except InvalidActionError as exc:
        return v2.invalid_action(exc)

    except (
        LLMClientError,
        DetectiveStorageError,
    ):
        logger.exception(
            "Gemini TTS V3 thất bại."
        )

        return fail(
            503,
            "TTS_UNAVAILABLE",
            "Cô chưa đọc được lúc này.",
        )

    except (
        APIError,
        httpx.RequestError,
        ValueError,
        ValidationError,
    ):
        logger.exception(
            "Không xử lý được narration V3."
        )

        return v2.database_error()

    # --------------------------------------------------------
    # 11. Tương thích V2
    #
    # Phải nằm NGOÀI narration_lock bên trên
    # để không deadlock với V2.
    # --------------------------------------------------------

    return await v2.narration(
        case_id,
        parsed,
        db,
    )

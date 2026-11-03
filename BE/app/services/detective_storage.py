
# ============================================================
# FILE: BE/app/services/detective_storage.py
# MODULE 3 — THÁM TỬ KHOA HỌC (v2)
#
# Chức năng:
#   1. Upload ảnh nền Cloudflare.
#   2. Upload ảnh cận cảnh của manh mối.
#   3. Upload giọng kể Gemini TTS dạng WAV.
#   4. Trả URL công khai để FE hiển thị/phát audio.
#   5. Dọn tất cả media khi xóa một vụ án cũ.
#
# Chỉ BE truy cập Supabase bằng SUPABASE_KEY;
# FE chỉ nhận các URL public của bucket demo.
# ============================================================

from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import quote
from uuid import uuid4

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

IMAGE_MIMES = {
    "image/png": "png",
    "image/jpeg": "jpg",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_AUDIO_BYTES = 10 * 1024 * 1024


class DetectiveStorageError(Exception):
    """Lỗi upload media của Module 3 lên Supabase Storage."""


def _safe_id(value: str, field_name: str) -> str:
    """Không cho ID trở thành đường dẫn chứa ../ hoặc ký tự đặc biệt."""
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,100}", value
    ):
        raise DetectiveStorageError(f"{field_name} không hợp lệ.")
    return value


def _case_folder(child_id: int, case_id: str | None) -> str:
    """Gom media theo hồ sơ và vụ án, tránh đụng file."""
    if type(child_id) is not int or child_id <= 0:
        raise DetectiveStorageError("child_id không hợp lệ.")

    folder = f"child-{child_id}"
    if case_id is not None:
        folder += f"/case-{_safe_id(case_id, 'case_id')}"
    return folder


def _bucket_url() -> str:
    settings = get_settings()
    bucket = quote(settings.DETECTIVE_STORAGE_BUCKET, safe="")
    return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}"


def public_image_url(path: str) -> str:
    """Đổi path trong Storage thành URL public (dùng cho ảnh và WAV)."""
    if not isinstance(path, str) or not path or path.startswith("/"):
        raise DetectiveStorageError("Đường dẫn media không hợp lệ.")

    settings = get_settings()
    bucket = quote(settings.DETECTIVE_STORAGE_BUCKET, safe="")
    return (
        f"{settings.SUPABASE_URL.rstrip('/')}"
        f"/storage/v1/object/public/{bucket}/{quote(path, safe='/')}"
    )


async def _upload_media(content: bytes, mime: str, path: str) -> str:
    """Helper dùng chung: ghi bytes vào một object mới trong bucket."""
    settings = get_settings()
    if not content:
        raise DetectiveStorageError("Media trống, không thể upload.")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": mime,
        "x-upsert": "false",  # Không ghi đè file đã có.
    }
    url = f"{_bucket_url()}/{quote(path, safe='/')}"

    try:
        async with httpx.AsyncClient(
            timeout=settings.DETECTIVE_STORAGE_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                url,
                headers=headers,
                content=content,
            )
            response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Upload Supabase Storage thất bại: HTTP %s (path=%s): %s",
            exc.response.status_code,
            path,
            exc.response.text[:300],
        )
        raise DetectiveStorageError("Không thể lưu media vụ án.") from exc

    except httpx.RequestError as exc:
        logger.warning("Không kết nối được Supabase Storage: %s", exc)
        raise DetectiveStorageError("Không kết nối được kho lưu trữ.") from exc

    return path


async def upload_background(
    image: bytes,
    mime: str,
    *,
    child_id: int,
    case_id: str | None = None,
) -> str:
    """Upload ảnh nền. Trả về storage path, không trả URL."""
    if mime not in IMAGE_MIMES or not image or len(image) > MAX_IMAGE_BYTES:
        raise DetectiveStorageError("Ảnh nền không hợp lệ hoặc quá lớn.")

    folder = _case_folder(child_id, case_id)
    path = f"{folder}/background/{uuid4().hex}.{IMAGE_MIMES[mime]}"
    return await _upload_media(image, mime, path)


async def upload_clue_image(
    image: bytes,
    mime: str,
    *,
    child_id: int,
    case_id: str,
    clue_id: str,
) -> str:
    """Upload ảnh cận cảnh. Chỉ lưu path trong media_manifest.clue_images."""
    if mime not in IMAGE_MIMES or not image or len(image) > MAX_IMAGE_BYTES:
        raise DetectiveStorageError("Ảnh manh mối không hợp lệ hoặc quá lớn.")

    folder = _case_folder(child_id, case_id)
    safe_clue_id = _safe_id(clue_id, "clue_id")
    path = (
        f"{folder}/clues/{safe_clue_id}-"
        f"{uuid4().hex}.{IMAGE_MIMES[mime]}"
    )
    return await _upload_media(image, mime, path)


async def upload_audio(
    wav: bytes,
    *,
    child_id: int,
    case_id: str,
    cache_key: str,
) -> str:
    """Upload WAV Gemini TTS; tên file được băm từ cache_key."""
    if (
        not isinstance(wav, bytes)
        or len(wav) < 44
        or len(wav) > MAX_AUDIO_BYTES
        or wav[:4] != b"RIFF"
        or wav[8:12] != b"WAVE"
    ):
        raise DetectiveStorageError("Audio WAV không hợp lệ hoặc quá lớn.")

    if not isinstance(cache_key, str) or not cache_key:
        raise DetectiveStorageError("Khóa cache audio không hợp lệ.")

    folder = _case_folder(child_id, case_id)
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

    # Hậu tố ngẫu nhiên tránh lỗi 409 nếu lần upload trước
    # đã thành công nhưng ghi cache vào DB thất bại.
    path = f"{folder}/audio/{digest}-{uuid4().hex[:8]}.wav"
    return await _upload_media(wav, "audio/wav", path)


async def _remove_paths(paths: list[str]) -> None:
    """Xóa hàng loạt object. Lỗi dọn dẹp chỉ ghi log, không phá luồng game."""
    valid_paths = list(dict.fromkeys(
        path
        for path in paths
        if isinstance(path, str)
        and path.startswith("child-")
        and not path.startswith("fallback/")
    ))
    if not valid_paths:
        return

    settings = get_settings()
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.DETECTIVE_STORAGE_TIMEOUT_SECONDS
        ) as client:
            response = await client.request(
                "DELETE",
                _bucket_url(),
                headers=headers,
                json={"prefixes": valid_paths},
            )
            response.raise_for_status()

    except httpx.HTTPError as exc:
        logger.warning("Không xóa được media cũ trong Storage: %s", exc)


async def remove_background(path: str) -> None:
    """Giữ tương thích với hàm xóa ảnh nền phiên bản cũ."""
    await _remove_paths([path])


async def remove_case_media(
    image_path: str,
    manifest: dict | None = None,
) -> None:
    """Xóa nền + ảnh clue + audio của vụ án sau khi xóa case khỏi DB."""
    paths: list[str] = [image_path]

    if isinstance(manifest, dict):
        for key in ("clue_images", "audio"):
            entries = manifest.get(key)
            if isinstance(entries, dict):
                paths.extend(
                    value for value in entries.values()
                    if isinstance(value, str)
                )

    await _remove_paths(paths)


def background_url(path: str) -> str:
    """Ảnh Cloudflare dùng public URL; fallback SVG dùng URL của BE."""
    if path.startswith("fallback/"):
        scene_id = path.removeprefix("fallback/").removesuffix(".svg")

        if scene_id not in ("classroom", "garden", "lab"):
            raise DetectiveStorageError("Ảnh SVG dự phòng không hợp lệ.")

        return f"/api/detective/backgrounds/{scene_id}.svg"

    return public_image_url(path)

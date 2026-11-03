
"""
Kiểm thử thực tế TTS.

Chạy:
python scripts/smoke_detective_tts.py \
    --case-id UUID --child-id 101

Lần đầu có thể tiêu hao quota Gemini.
Lần thứ hai phải dùng cache.
"""

import argparse
import json
import urllib.error
import urllib.request


def post(
    base,
    case_id,
    child_id,
    kind,
    segment_id=None,
):
    url = (
        f"{base.rstrip('/')}"
        f"/api/detective/{case_id}/narration"
    )

    body = json.dumps({
        "child_id": child_id,
        "segment_type": kind,
        "segment_id": segment_id,
    }).encode()

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:
            return (
                response.status,
                json.load(response),
            )

    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            json.load(exc),
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case-id",
        required=True,
    )

    parser.add_argument(
        "--child-id",
        required=True,
        type=int,
    )

    parser.add_argument(
        "--base",
        default="http://127.0.0.1:8000",
    )

    args = parser.parse_args()

    first_status, first = post(
        args.base,
        args.case_id,
        args.child_id,
        "introduction",
    )

    print(
        "Lần 1:",
        first_status,
        first.get("message"),
    )

    assert first_status == 200, (
        "TTS chưa chạy; kiểm tra model/quota/.env"
    )

    second_status, second = post(
        args.base,
        args.case_id,
        args.child_id,
        "introduction",
    )

    print(
        "Lần 2:",
        second_status,
        second.get("data"),
    )

    assert second_status == 200

    assert second["data"]["cached"] is True

    assert (
        first["data"]["audio_url"]
        == second["data"]["audio_url"]
    )

    wrong_status, _ = post(
        args.base,
        args.case_id,
        args.child_id + 999999,
        "introduction",
    )

    assert wrong_status == 404

    # Kiểm tra quyền đọc lời giải.
    status, payload = post(
        args.base,
        args.case_id,
        args.child_id,
        "final_explanation",
    )

    print(
        "Yêu cầu lời giải:",
        status,
        payload.get("message"),
    )

    assert status in (200, 422)

    print("SMOKE TTS OK")


if __name__ == "__main__":
    main()

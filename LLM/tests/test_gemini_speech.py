
import io
import wave

import pytest

from app.providers.gemini_speech import (
    pcm_to_wav,
)

from app.errors import LLMProviderError


def test_pcm_wav_header_and_frequency():
    blob = pcm_to_wav(
        b"\x00\x00" * 100,
        24000,
    )

    assert blob[:4] == b"RIFF"
    assert blob[8:12] == b"WAVE"

    with wave.open(
        io.BytesIO(blob),
        "rb",
    ) as file:
        assert file.getnchannels() == 1
        assert file.getsampwidth() == 2
        assert file.getframerate() == 24000
        assert file.getnframes() == 100


def test_pcm_rejects_invalid_data():
    with pytest.raises(LLMProviderError):
        pcm_to_wav(b"\x00")

    with pytest.raises(LLMProviderError):
        pcm_to_wav(
            b"\x00\x00",
            rate=1000,
        )

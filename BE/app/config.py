
from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # LLM Server dùng chung
    LLM_SERVER_URL: str = "http://127.0.0.1:8001"

    LLM_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        gt=0,
    )

    LLM_GENERATION_MODEL: str = "default"
    LLM_EVALUATION_MODEL: str = "default"

    LLM_INTERNAL_API_KEY: str | None = None

    # Module 3 — Cloudflare image
    LLM_IMAGE_TIMEOUT_SECONDS: float = Field(
        default=120.0,
        gt=0,
    )

    DETECTIVE_MAX_EXTRA_IMAGES: int = Field(
        default=2,
        ge=0,
        le=2,
    )

    DETECTIVE_STORAGE_BUCKET: str = (
        "detective-backgrounds"
    )

    DETECTIVE_STORAGE_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        gt=0,
    )

    # Module 3 — Gemini TTS
    DETECTIVE_TTS_ENABLED: bool = True

    DETECTIVE_TTS_CACHE_VERSION: str = "v1"

    LLM_TTS_TIMEOUT_SECONDS: float = Field(
        default=100.0,
        gt=0,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

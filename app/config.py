"""Application configuration loaded from environment variables.

The OCR model itself is served separately via sglang. This service only needs
to know how to reach that sglang OpenAI-compatible endpoint, which is provided
entirely through environment variables (see ``.env.example``).
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- sglang server -----------------------------------------------------
    # Server root URL. The ``/v1/chat/completions`` path is appended
    # automatically, so a trailing ``/v1`` is optional here.
    # Example: http://sglang:30000
    sglang_base_url: str = Field(
        default="http://localhost:30000",
        alias="SGLANG_BASE_URL",
    )
    # API key for the sglang server. Sent as a Bearer token when set to a
    # non-empty value other than "EMPTY". sglang servers launched without
    # ``--api-key`` need no key.
    sglang_api_key: str = Field(default="", alias="SGLANG_API_KEY")

    # Served model name as registered in sglang.
    ocr_model: str = Field(default="Unlimited-OCR", alias="OCR_MODEL")

    # --- behaviour ---------------------------------------------------------
    # Max concurrent in-flight OCR calls to the sglang server (each uploaded
    # PDF / image-document is one call).
    max_concurrency: int = Field(default=4, alias="OCR_MAX_CONCURRENCY")
    # HTTP timeout (seconds) for a single OCR call.
    request_timeout: float = Field(default=1200.0, alias="OCR_REQUEST_TIMEOUT")

    # --- PDF rendering -----------------------------------------------------
    pdf_dpi: int = Field(default=300, alias="PDF_DPI")

    # --- upload limits -----------------------------------------------------
    max_file_size_mb: float = Field(default=50.0, alias="MAX_FILE_SIZE_MB")
    max_files: int = Field(default=20, alias="MAX_FILES")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

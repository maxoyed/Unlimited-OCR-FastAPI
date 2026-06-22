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

    # --- sglang OpenAI-compatible endpoint --------------------------------
    # Base URL of the sglang server. Must point at the OpenAI-compatible API
    # root (i.e. include the trailing ``/v1``). Example: http://sglang:30000/v1
    sglang_base_url: str = Field(
        default="http://localhost:30000/v1",
        alias="SGLANG_BASE_URL",
    )
    # API key for the sglang server. sglang accepts any non-empty value unless
    # it was launched with ``--api-key``; "EMPTY" is the common placeholder.
    sglang_api_key: str = Field(default="EMPTY", alias="SGLANG_API_KEY")

    # Served model name as registered in sglang. Override to match whatever
    # ``--served-model-name`` (or the model path) your sglang server exposes.
    ocr_model: str = Field(default="baidu/Unlimited-OCR", alias="OCR_MODEL")

    # --- OCR behaviour ----------------------------------------------------
    # Default instruction sent alongside each image. Override per-request via
    # the ``prompt`` form field.
    ocr_prompt: str = Field(
        default="OCR this image. Return all text content faithfully.",
        alias="OCR_PROMPT",
    )
    max_tokens: int = Field(default=8192, alias="OCR_MAX_TOKENS")
    temperature: float = Field(default=0.0, alias="OCR_TEMPERATURE")

    # Max number of concurrent in-flight requests to the sglang server. Pages
    # of a PDF and multiple uploaded images are processed concurrently up to
    # this limit.
    max_concurrency: int = Field(default=8, alias="OCR_MAX_CONCURRENCY")
    # HTTP timeout (seconds) for a single request to the sglang server.
    request_timeout: float = Field(default=300.0, alias="OCR_REQUEST_TIMEOUT")

    # --- PDF rendering ----------------------------------------------------
    # Resolution used when rasterising PDF pages to images before OCR.
    pdf_dpi: int = Field(default=200, alias="PDF_DPI")

    # --- Upload limits ----------------------------------------------------
    # Per-file size limit in megabytes. 0 disables the check.
    max_file_size_mb: float = Field(default=50.0, alias="MAX_FILE_SIZE_MB")
    # Max number of files accepted per request. 0 disables the check.
    max_files: int = Field(default=20, alias="MAX_FILES")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

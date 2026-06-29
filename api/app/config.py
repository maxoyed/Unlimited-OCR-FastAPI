"""Application configuration loaded from environment variables.

The OCR model itself is served separately via vLLM. This service only needs
to know how to reach that vLLM OpenAI-compatible endpoint, which is provided
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

    # --- vLLM server -------------------------------------------------------
    # Server root URL. The ``/v1/chat/completions`` path is appended
    # automatically, so a trailing ``/v1`` is optional here.
    # Example: http://vllm:8000
    vllm_base_url: str = Field(
        default="http://localhost:8000",
        alias="VLLM_BASE_URL",
    )
    # API key for the vLLM server. Sent as a Bearer token when set to a
    # non-empty value other than "EMPTY". vLLM servers launched without
    # ``--api-key`` need no key.
    vllm_api_key: str = Field(default="", alias="VLLM_API_KEY")

    # Served model name as registered in vLLM.
    ocr_model: str = Field(default="baidu/Unlimited-OCR", alias="OCR_MODEL")

    # --- behaviour ---------------------------------------------------------
    # Max concurrent in-flight OCR calls to the vLLM server (each uploaded
    # PDF / image-document is one call).
    max_concurrency: int = Field(default=4, alias="OCR_MAX_CONCURRENCY")
    # HTTP timeout (seconds) for a single OCR call.
    request_timeout: float = Field(default=1200.0, alias="OCR_REQUEST_TIMEOUT")
    # Max tokens to generate per OCR call.
    max_tokens: int = Field(default=8192, alias="OCR_MAX_TOKENS")

    # --- PDF rendering -----------------------------------------------------
    pdf_dpi: int = Field(default=300, alias="PDF_DPI")

    # --- upload limits -----------------------------------------------------
    max_file_size_mb: float = Field(default=50.0, alias="MAX_FILE_SIZE_MB")
    max_files: int = Field(default=20, alias="MAX_FILES")

    # --- CORS --------------------------------------------------------------
    # Comma-separated list of allowed origins for the browser demo frontend.
    # Default "*" allows any origin (the API uses no cookies/credentials).
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_allow_origins.split(",")]
        return [o for o in origins if o]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

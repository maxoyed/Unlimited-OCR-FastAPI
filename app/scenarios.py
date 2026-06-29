"""Fixed per-scenario OCR parameters.

Prompts and n-gram window sizes are hardcoded to mirror the official
Unlimited-OCR usage. They are intentionally NOT user-configurable.

Under vLLM the gundam (crop) vs base mode is chosen automatically from the
number of images, so ``image_mode`` here is purely descriptive (reported back
to the caller) — it is never sent to the server.
"""

from dataclasses import dataclass

# Fixed n-gram size used by the official example.
NGRAM_SIZE: int = 35


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    image_mode: str  # descriptive only: "gundam" (single image) or "base"
    window_size: int


# Single image -> vLLM uses gundam (crop) mode automatically.
SINGLE_IMAGE = Scenario(
    name="single_image",
    prompt="document parsing.",
    image_mode="gundam",
    window_size=128,
)

# Multiple images in one document -> vLLM falls back to base mode automatically.
MULTI_IMAGE = Scenario(
    name="multi_image",
    prompt="Multi page parsing.",
    image_mode="base",
    window_size=1024,
)

# PDF, rasterised to one image per page -> base mode.
PDF = Scenario(
    name="pdf",
    prompt="Multi page parsing.",
    image_mode="base",
    window_size=1024,
)

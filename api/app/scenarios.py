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

# Multiple images in one document -> each image is OCR'd individually in gundam
# (crop) mode and the results are concatenated, for the same reason as PDFs:
# one "Multi page parsing." base-mode request over all images degenerates into
# runaway repetition on a dense image, so we parse image-by-image instead.
MULTI_IMAGE = Scenario(
    name="multi_image",
    prompt="document parsing.",
    image_mode="gundam",
    window_size=128,
)

# PDF, rasterised to one image per page -> each page is OCR'd individually in
# gundam (crop) mode, exactly like a single image. Sending every page in one
# "Multi page parsing." base-mode request lets the model degenerate into
# runaway repetition on a dense page and burn the whole token budget, so we
# parse page-by-page and concatenate the results.
PDF = Scenario(
    name="pdf",
    prompt="document parsing.",
    image_mode="gundam",
    window_size=128,
)

"""Fixed per-scenario OCR parameters.

Prompts, image modes and n-gram window sizes are hardcoded to mirror the
official Unlimited-OCR usage. They are intentionally NOT user-configurable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    image_mode: str  # "gundam" or "base"
    window_size: int


# Single image. Supports two configs: "gundam" (default) or "base".
SINGLE_IMAGE = Scenario(
    name="single_image",
    prompt="document parsing.",
    image_mode="gundam",
    window_size=128,
)
SINGLE_IMAGE_BASE = Scenario(
    name="single_image",
    prompt="document parsing.",
    image_mode="base",
    window_size=1024,
)

# Multiple images in one document ("base" only).
MULTI_IMAGE = Scenario(
    name="multi_image",
    prompt="Multi page parsing.",
    image_mode="base",
    window_size=1024,
)

# PDF, rasterised to one image per page ("base" only).
PDF = Scenario(
    name="pdf",
    prompt="Multi page parsing.",
    image_mode="base",
    window_size=1024,
)

"""Pydantic response models for the OCR API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentResult(BaseModel):
    name: str = Field(..., description="Source filename(s) for this document.")
    scenario: str = Field(
        ..., description="OCR scenario: 'single_image', 'multi_image', or 'pdf'."
    )
    image_mode: str = Field(..., description="sglang image mode used ('gundam'/'base').")
    page_count: int = Field(..., description="Number of images sent to the model.")
    text: str = Field(..., description="Extracted text for the whole document.")
    error: Optional[str] = Field(
        default=None, description="Error message if this document failed."
    )


class OCRResponse(BaseModel):
    model: str
    results: List[DocumentResult]


class HealthResponse(BaseModel):
    status: str
    model: str
    sglang_base_url: str

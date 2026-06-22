"""Pydantic response models for the OCR API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class PageResult(BaseModel):
    page: int = Field(..., description="1-based page/image index within the file.")
    text: str = Field(..., description="Extracted text for this page.")
    error: Optional[str] = Field(
        default=None, description="Error message if this page failed to process."
    )


class FileResult(BaseModel):
    filename: str
    type: str = Field(..., description="Detected file kind: 'image' or 'pdf'.")
    page_count: int
    text: str = Field(..., description="All pages concatenated with separators.")
    pages: List[PageResult]
    error: Optional[str] = Field(
        default=None, description="File-level error if the whole file failed."
    )


class OCRResponse(BaseModel):
    model: str
    results: List[FileResult]


class HealthResponse(BaseModel):
    status: str
    model: str
    sglang_base_url: str

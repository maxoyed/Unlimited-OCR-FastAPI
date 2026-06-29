"""Helpers for turning uploaded files into base64 image content parts."""

import base64
from typing import List

import fitz  # PyMuPDF

IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/gif",
}
IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".gif",
}
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_EXTENSIONS = {".pdf"}


def _ext(filename: str) -> str:
    name = (filename or "").lower()
    return name[name.rfind(".") :] if "." in name else ""


def detect_kind(filename: str, content_type: str | None) -> str:
    """Return 'image', 'pdf', or 'unknown' for an uploaded file."""
    ext = _ext(filename)
    ctype = (content_type or "").lower().split(";")[0].strip()

    if ctype in PDF_CONTENT_TYPES or ext in PDF_EXTENSIONS:
        return "pdf"
    if ctype in IMAGE_CONTENT_TYPES or ext in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def _mime_for_image(filename: str, content_type: str | None) -> str:
    ext = _ext(filename)
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext in (".tif", ".tiff"):
        return "image/tiff"
    if ext:
        return f"image/{ext.lstrip('.')}"
    ctype = (content_type or "").lower().split(";")[0].strip()
    return ctype or "image/png"


def image_content_part(data: bytes, filename: str, content_type: str | None) -> dict:
    """Build an OpenAI-style image_url content part from raw image bytes."""
    mime = _mime_for_image(filename, content_type)
    b64 = base64.b64encode(data).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def png_content_part(png_bytes: bytes) -> dict:
    """Build an image_url content part from PNG bytes (used for PDF pages)."""
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}


def pdf_to_png_pages(data: bytes, dpi: int) -> List[bytes]:
    """Rasterise every page of a PDF into PNG bytes (one entry per page)."""
    pages: List[bytes] = []
    zoom = dpi / 72.0  # PDF user space is 72 DPI.
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(pix.tobytes("png"))
    return pages

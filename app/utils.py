"""Helpers for turning uploaded files into OCR-ready PNG images."""

import io
from typing import List

import fitz  # PyMuPDF
from PIL import Image

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


def detect_kind(filename: str, content_type: str | None) -> str:
    """Return 'image', 'pdf', or 'unknown' for an uploaded file."""
    name = (filename or "").lower()
    ext = name[name.rfind(".") :] if "." in name else ""
    ctype = (content_type or "").lower().split(";")[0].strip()

    if ctype in PDF_CONTENT_TYPES or ext in PDF_EXTENSIONS:
        return "pdf"
    if ctype in IMAGE_CONTENT_TYPES or ext in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def image_bytes_to_png(data: bytes) -> bytes:
    """Validate/normalise arbitrary image bytes into RGB PNG bytes."""
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()


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

"""FastAPI application exposing OCR endpoints backed by an sglang model."""

import asyncio
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from . import __version__
from .config import settings
from .ocr import ocr_png, ocr_png_batch
from .schemas import FileResult, HealthResponse, OCRResponse, PageResult
from .utils import detect_kind, image_bytes_to_png, pdf_to_png_pages

app = FastAPI(
    title="Unlimited-OCR FastAPI",
    description=(
        "Upload one or more images / PDFs and extract text using a "
        "Baidu Unlimited-OCR model served via sglang."
    ),
    version=__version__,
)

PAGE_SEPARATOR = "\n\n"


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.ocr_model,
        sglang_base_url=settings.sglang_base_url,
    )


def _check_size(data: bytes, filename: str) -> None:
    if settings.max_file_size_mb > 0:
        limit = settings.max_file_size_mb * 1024 * 1024
        if len(data) > limit:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File '{filename}' is {len(data) / 1024 / 1024:.1f} MB, "
                    f"exceeding the {settings.max_file_size_mb} MB limit."
                ),
            )


async def _process_file(upload: UploadFile, prompt: Optional[str]) -> FileResult:
    filename = upload.filename or "upload"
    data = await upload.read()
    _check_size(data, filename)

    kind = detect_kind(filename, upload.content_type)
    if kind == "unknown":
        return FileResult(
            filename=filename,
            type="unknown",
            page_count=0,
            text="",
            pages=[],
            error=(
                "Unsupported file type. Provide an image "
                "(png/jpg/webp/bmp/tiff/gif) or a PDF."
            ),
        )

    try:
        if kind == "pdf":
            page_images = pdf_to_png_pages(data, settings.pdf_dpi)
        else:
            page_images = [image_bytes_to_png(data)]
    except Exception as exc:  # noqa: BLE001 - report decode/render failures
        return FileResult(
            filename=filename,
            type=kind,
            page_count=0,
            text="",
            pages=[],
            error=f"Failed to read file: {exc}",
        )

    if not page_images:
        return FileResult(
            filename=filename,
            type=kind,
            page_count=0,
            text="",
            pages=[],
            error="No renderable pages found.",
        )

    results = await asyncio.gather(
        *(ocr_png(img, prompt) for img in page_images),
        return_exceptions=True,
    )

    pages: List[PageResult] = []
    texts: List[str] = []
    for idx, res in enumerate(results, start=1):
        if isinstance(res, Exception):
            pages.append(PageResult(page=idx, text="", error=str(res)))
        else:
            pages.append(PageResult(page=idx, text=res))
            texts.append(res)

    return FileResult(
        filename=filename,
        type=kind,
        page_count=len(page_images),
        text=PAGE_SEPARATOR.join(texts),
        pages=pages,
    )


@app.post("/ocr", response_model=OCRResponse)
async def ocr(
    files: List[UploadFile] = File(
        ..., description="One or more image and/or PDF files."
    ),
    prompt: Optional[str] = Form(
        default=None,
        description="Optional prompt override sent to the OCR model.",
    ),
) -> OCRResponse:
    """OCR one or many uploaded images/PDFs in a single request."""
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    if settings.max_files > 0 and len(files) > settings.max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files: {len(files)} > {settings.max_files} limit.",
        )

    results = [await _process_file(f, prompt) for f in files]
    return OCRResponse(model=settings.ocr_model, results=results)


@app.post("/ocr/image", response_model=OCRResponse)
async def ocr_image(
    files: List[UploadFile] = File(..., description="One or more image files."),
    prompt: Optional[str] = Form(default=None),
) -> OCRResponse:
    """OCR endpoint restricted to image uploads."""
    return await ocr(files=files, prompt=prompt)


@app.post("/ocr/pdf", response_model=OCRResponse)
async def ocr_pdf(
    files: List[UploadFile] = File(..., description="One or more PDF files."),
    prompt: Optional[str] = Form(default=None),
) -> OCRResponse:
    """OCR endpoint restricted to PDF uploads."""
    return await ocr(files=files, prompt=prompt)

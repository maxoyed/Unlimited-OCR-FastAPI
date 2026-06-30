"""FastAPI application exposing OCR endpoints backed by a vLLM model.

Prompts and sampling parameters are fixed per scenario (see ``scenarios.py``)
and are not user-configurable, matching the official Unlimited-OCR usage:

* single image  -> "document parsing."   (gundam, window 128)
* multiple images -> "Multi page parsing." (base, window 1024) as one document
* PDF           -> "document parsing." (gundam, window 128) per page, the page
  texts concatenated into one document
"""

import asyncio
from typing import List, Optional, Tuple

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from . import scenarios
from .config import settings
from .ocr import run_ocr
from .schemas import DocumentResult, HealthResponse, OCRResponse
from .utils import (
    detect_kind,
    image_content_part,
    pdf_to_png_pages,
    png_content_part,
)

app = FastAPI(
    title="Unlimited-OCR FastAPI",
    description=(
        "Upload single/multiple images or PDFs and extract text using a "
        "Baidu Unlimited-OCR model served via vLLM."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.ocr_model,
        vllm_base_url=settings.vllm_base_url,
    )


async def _read_checked(upload: UploadFile) -> bytes:
    data = await upload.read()
    if settings.max_file_size_mb > 0:
        limit = settings.max_file_size_mb * 1024 * 1024
        if len(data) > limit:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File '{upload.filename}' is {len(data) / 1024 / 1024:.1f} MB, "
                    f"exceeding the {settings.max_file_size_mb} MB limit."
                ),
            )
    return data


def _enforce_file_count(files: List[UploadFile]) -> None:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    if settings.max_files > 0 and len(files) > settings.max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files: {len(files)} > {settings.max_files} limit.",
        )


async def _ocr_parts_individually(
    parts: List[dict], labels: List[str]
) -> Tuple[str, Optional[str]]:
    """OCR each image part on its own (gundam) and concatenate the texts.

    One request per part gives every page/image the higher effective resolution
    of single-image parsing and isolates a hard item: repetition degeneration
    or an upstream failure stays contained to its own page instead of corrupting
    the whole document. Calls run concurrently, throttled by run_ocr's shared
    semaphore. ``labels`` name each part for error reporting (e.g. "page 3" or
    "image 2 (foo.png)"); a failed part is dropped from the text and recorded.
    """
    results = await asyncio.gather(
        *(run_ocr(scenarios.SINGLE_IMAGE, [part]) for part in parts),
        return_exceptions=True,
    )

    texts: List[str] = []
    errors: List[str] = []
    for label, res in zip(labels, results):
        if isinstance(res, Exception):
            errors.append(f"{label}: {res}")
        elif res:
            texts.append(res)

    return "\n\n".join(texts), ("; ".join(errors) if errors else None)


async def _ocr_images(uploads: List[UploadFile]) -> DocumentResult:
    """OCR one (single) or many images, each parsed individually in gundam mode."""
    parts = []
    names = []
    for up in uploads:
        data = await _read_checked(up)
        parts.append(image_content_part(data, up.filename or "image", up.content_type))
        names.append(up.filename or "image")

    if len(uploads) == 1:
        scenario = scenarios.SINGLE_IMAGE
        name = names[0]
        labels = [names[0]]
    else:
        scenario = scenarios.MULTI_IMAGE
        name = f"{len(names)} images: " + ", ".join(names)
        labels = [f"image {i + 1} ({names[i]})" for i in range(len(names))]

    text, error = await _ocr_parts_individually(parts, labels)
    return DocumentResult(
        name=name,
        scenario=scenario.name,
        image_mode=scenario.image_mode,
        page_count=len(parts),
        text=text,
        error=error,
    )


async def _ocr_pdf(upload: UploadFile) -> DocumentResult:
    """OCR a single PDF, parsing each rasterised page individually in gundam mode."""
    name = upload.filename or "document.pdf"
    scenario = scenarios.PDF
    try:
        data = await _read_checked(upload)
        pages = pdf_to_png_pages(data, settings.pdf_dpi)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - report render/decode failures
        return DocumentResult(
            name=name,
            scenario=scenario.name,
            image_mode=scenario.image_mode,
            page_count=0,
            text="",
            error=f"Failed to read PDF: {exc}",
        )

    if not pages:
        return DocumentResult(
            name=name,
            scenario=scenario.name,
            image_mode=scenario.image_mode,
            page_count=0,
            text="",
            error="No pages found in PDF.",
        )

    parts = [png_content_part(p) for p in pages]
    labels = [f"page {i + 1}" for i in range(len(parts))]
    text, error = await _ocr_parts_individually(parts, labels)
    return DocumentResult(
        name=name,
        scenario=scenario.name,
        image_mode=scenario.image_mode,
        page_count=len(parts),
        text=text,
        error=error,
    )


@app.post("/ocr/image", response_model=OCRResponse)
async def ocr_image(
    files: List[UploadFile] = File(..., description="One or more image files."),
) -> OCRResponse:
    """OCR images. One image -> single parse; many -> one multi-page document."""
    _enforce_file_count(files)
    for f in files:
        if detect_kind(f.filename or "", f.content_type) != "image":
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}' is not a supported image file.",
            )
    result = await _ocr_images(files)
    return OCRResponse(model=settings.ocr_model, results=[result])


@app.post("/ocr/pdf", response_model=OCRResponse)
async def ocr_pdf(
    files: List[UploadFile] = File(..., description="One or more PDF files."),
) -> OCRResponse:
    """OCR PDFs. Each PDF is one multi-page document."""
    _enforce_file_count(files)
    for f in files:
        if detect_kind(f.filename or "", f.content_type) != "pdf":
            raise HTTPException(
                status_code=400, detail=f"'{f.filename}' is not a PDF file."
            )
    results = await asyncio.gather(*(_ocr_pdf(f) for f in files))
    return OCRResponse(model=settings.ocr_model, results=list(results))


@app.post("/ocr", response_model=OCRResponse)
async def ocr(
    files: List[UploadFile] = File(
        ..., description="One or more image and/or PDF files."
    ),
) -> OCRResponse:
    """Generic endpoint: images become one image-document, each PDF its own."""
    _enforce_file_count(files)

    images: List[UploadFile] = []
    pdfs: List[UploadFile] = []
    unknown: List[str] = []
    for f in files:
        kind = detect_kind(f.filename or "", f.content_type)
        if kind == "image":
            images.append(f)
        elif kind == "pdf":
            pdfs.append(f)
        else:
            unknown.append(f.filename or "upload")

    if unknown:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file(s): "
                + ", ".join(unknown)
                + ". Provide images (png/jpg/webp/bmp/tiff/gif) or PDFs."
            ),
        )

    tasks = []
    if images:
        tasks.append(_ocr_images(images))
    tasks.extend(_ocr_pdf(f) for f in pdfs)
    results = await asyncio.gather(*tasks)
    return OCRResponse(model=settings.ocr_model, results=list(results))

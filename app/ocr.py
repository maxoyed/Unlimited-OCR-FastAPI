"""Thin async client around the sglang OpenAI-compatible endpoint."""

import asyncio
import base64
from typing import List, Optional

from openai import AsyncOpenAI

from .config import settings

_client = AsyncOpenAI(
    base_url=settings.sglang_base_url,
    api_key=settings.sglang_api_key,
    timeout=settings.request_timeout,
    max_retries=2,
)

_semaphore = asyncio.Semaphore(settings.max_concurrency)


def _data_url(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


async def ocr_png(png_bytes: bytes, prompt: Optional[str] = None) -> str:
    """Run OCR on a single PNG image and return the extracted text."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt or settings.ocr_prompt},
                {"type": "image_url", "image_url": {"url": _data_url(png_bytes)}},
            ],
        }
    ]
    async with _semaphore:
        resp = await _client.chat.completions.create(
            model=settings.ocr_model,
            messages=messages,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        )
    return (resp.choices[0].message.content or "").strip()


async def ocr_png_batch(
    pages: List[bytes], prompt: Optional[str] = None
) -> List[str]:
    """Run OCR over many images concurrently, preserving input order."""
    tasks = [ocr_png(p, prompt) for p in pages]
    return await asyncio.gather(*tasks)

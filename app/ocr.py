"""Async client around the sglang OpenAI-compatible endpoint.

Mirrors the official Unlimited-OCR request shape: fixed temperature, the
embedded DeepSeek-OCR no-repeat-ngram custom logit processor, an
``images_config.image_mode`` and per-scenario ``custom_params``. Requests are
streamed and the SSE deltas are aggregated into the final text.
"""

import asyncio
import json
from typing import List

import httpx

from .config import settings
from .logit_processor import CUSTOM_LOGIT_PROCESSOR, NGRAM_SIZE
from .scenarios import Scenario

_semaphore = asyncio.Semaphore(settings.max_concurrency)


def _endpoint() -> str:
    base = settings.sglang_base_url.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/v1/chat/completions"


def _headers() -> dict:
    headers = {"Content-Type": "application/json"}
    key = settings.sglang_api_key.strip()
    if key and key.upper() != "EMPTY":
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _payload(scenario: Scenario, content_parts: List[dict]) -> dict:
    return {
        "model": settings.ocr_model,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": scenario.prompt}, *content_parts],
            }
        ],
        "temperature": 0,
        "skip_special_tokens": False,
        "images_config": {"image_mode": scenario.image_mode},
        "custom_logit_processor": CUSTOM_LOGIT_PROCESSOR,
        "custom_params": {
            "ngram_size": NGRAM_SIZE,
            "window_size": scenario.window_size,
        },
        "stream": True,
    }


async def run_ocr(scenario: Scenario, content_parts: List[dict]) -> str:
    """Run one OCR generation (one document) and return the aggregated text."""
    payload = _payload(scenario, content_parts)
    chunks: List[str] = []
    async with _semaphore:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            async with client.stream(
                "POST", _endpoint(), headers=_headers(), json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[len("data: ") :]
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    delta = event["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        chunks.append(delta)
    return "".join(chunks).strip()

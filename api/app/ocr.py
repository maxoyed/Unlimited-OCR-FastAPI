"""Async client around the vLLM OpenAI-compatible endpoint.

Mirrors the official Unlimited-OCR vLLM request shape: fixed temperature, the
literal ``<image>`` prompt prefix, ``skip_special_tokens=False`` and the
DeepSeek-OCR no-repeat-ngram parameters passed via ``vllm_xargs``. The
no-repeat-ngram logits processor itself is registered on the vLLM server
(``--logits_processors``), so nothing about it is sent per request. Requests are
streamed and the SSE deltas are aggregated into the final text.
"""

import asyncio
import json
from typing import List

import httpx

from .config import settings
from .scenarios import NGRAM_SIZE, Scenario

_semaphore = asyncio.Semaphore(settings.max_concurrency)


def _endpoint() -> str:
    base = settings.vllm_base_url.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/v1/chat/completions"


def _headers() -> dict:
    headers = {"Content-Type": "application/json"}
    key = settings.vllm_api_key.strip()
    if key and key.upper() != "EMPTY":
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _payload(scenario: Scenario, content_parts: List[dict]) -> dict:
    # The prompt text MUST begin with a literal "<image>" or the model returns
    # empty output. gundam (crop) vs base mode is chosen automatically by vLLM
    # based on the number of images, so no image_mode is sent.
    return {
        "model": settings.ocr_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"<image>{scenario.prompt}"},
                    *content_parts,
                ],
            }
        ],
        "max_tokens": settings.max_tokens,
        "temperature": 0,
        "skip_special_tokens": False,
        "vllm_xargs": {
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

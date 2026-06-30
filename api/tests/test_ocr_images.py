"""Behaviour tests for the image OCR path in ``app.main``.

A single image is parsed in one gundam request. Multiple images must be parsed
one image at a time (also gundam) rather than crammed into one base-mode
request, for the same reason as PDFs: one request per item reads dense pages at
full resolution and isolates a failure (or repetition degeneration) to its own
image instead of corrupting the whole batch.
"""

from dataclasses import dataclass

import pytest

from app import main


@dataclass
class _FakeImageUpload:
    filename: str
    content_type: str = "image/png"
    data: bytes = b""

    async def read(self) -> bytes:
        return self.data


@pytest.fixture(autouse=True)
def passthrough_image_parts(monkeypatch):
    """Make image_content_part return the raw bytes so calls trace to uploads."""
    monkeypatch.setattr(
        main, "image_content_part", lambda data, filename, ctype: data
    )


async def test_single_image_is_one_gundam_call(monkeypatch):
    calls = []

    async def fake_run_ocr(scenario, parts):
        calls.append((scenario, parts))
        return "single-text"

    monkeypatch.setattr(main, "run_ocr", fake_run_ocr)

    result = await main._ocr_images([_FakeImageUpload("x.png", data=b"only")])

    assert len(calls) == 1
    assert calls[0][1] == [b"only"]
    assert result.scenario == "single_image"
    assert result.image_mode == "gundam"
    assert result.text == "single-text"
    assert result.page_count == 1
    assert result.error is None


async def test_multiple_images_are_ocrd_one_at_a_time_in_gundam_mode(monkeypatch):
    datas = [b"img-1", b"img-2", b"img-3"]
    calls = []

    async def fake_run_ocr(scenario, parts):
        calls.append((scenario, parts))
        idx = datas.index(parts[0]) + 1
        return f"text-{idx}"

    monkeypatch.setattr(main, "run_ocr", fake_run_ocr)

    uploads = [_FakeImageUpload(f"a{i}.png", data=d) for i, d in enumerate(datas)]
    result = await main._ocr_images(uploads)

    # One model call per image, never a single all-images request.
    assert len(calls) == len(datas)
    for scenario, parts in calls:
        assert scenario.image_mode == "gundam"
        assert scenario.prompt == "document parsing."
        assert len(parts) == 1
    assert sorted(parts[0] for _, parts in calls) == sorted(datas)

    # Texts concatenated in upload order; reported as a gundam multi_image doc.
    assert result.text == "text-1\n\ntext-2\n\ntext-3"
    assert result.scenario == "multi_image"
    assert result.image_mode == "gundam"
    assert result.page_count == 3
    assert result.error is None


async def test_one_failing_image_does_not_sink_the_batch(monkeypatch):
    datas = [b"img-1", b"img-2", b"img-3"]

    async def fake_run_ocr(scenario, parts):
        if parts[0] is datas[1]:  # second image blows up
            raise RuntimeError("vLLM 400")
        idx = datas.index(parts[0]) + 1
        return f"text-{idx}"

    monkeypatch.setattr(main, "run_ocr", fake_run_ocr)

    uploads = [_FakeImageUpload(f"a{i}.png", data=d) for i, d in enumerate(datas)]
    result = await main._ocr_images(uploads)

    assert result.text == "text-1\n\ntext-3"
    assert result.error is not None
    assert "image 2" in result.error
    assert "a1.png" in result.error
    assert result.page_count == 3

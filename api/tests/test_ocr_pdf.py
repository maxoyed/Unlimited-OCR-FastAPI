"""Behaviour tests for the PDF OCR path in ``app.main``.

A multi-page PDF must be OCR'd one page at a time in single-image (gundam)
mode rather than as a single base-mode generation. Sending every page in one
request lets the model degenerate into runaway repetition on a hard page and
burn the whole token budget; per-page gundam parsing reads dense pages cleanly
and isolates a failure to its own page.
"""

from dataclasses import dataclass

import pytest

from app import main


@dataclass
class _FakeUpload:
    filename: str
    content_type: str = "application/pdf"
    data: bytes = b"%PDF-fake"

    async def read(self) -> bytes:
        return self.data


@pytest.fixture
def fake_pages(monkeypatch):
    """Render any PDF to three deterministic pages; image parts pass through."""
    pages = [b"page-1-png", b"page-2-png", b"page-3-png"]
    monkeypatch.setattr(main, "pdf_to_png_pages", lambda data, dpi: pages)
    # Identity wrapping so a run_ocr call can be traced back to its page.
    monkeypatch.setattr(main, "png_content_part", lambda page: page)
    return pages


async def test_pdf_is_ocrd_one_page_at_a_time_in_gundam_mode(fake_pages, monkeypatch):
    calls = []

    async def fake_run_ocr(scenario, parts):
        calls.append((scenario, parts))
        idx = fake_pages.index(parts[0]) + 1
        return f"text-of-page-{idx}"

    monkeypatch.setattr(main, "run_ocr", fake_run_ocr)

    result = await main._ocr_pdf(_FakeUpload(filename="doc.pdf"))

    # One model call per page, never a single all-pages request.
    assert len(calls) == len(fake_pages)
    # Each call is single-image gundam mode with exactly one page attached.
    for scenario, parts in calls:
        assert scenario.image_mode == "gundam"
        assert scenario.prompt == "document parsing."
        assert len(parts) == 1
    # Every page was sent exactly once.
    assert sorted(parts[0] for _, parts in calls) == sorted(fake_pages)

    # Page texts are concatenated in page order, document reported as gundam PDF.
    assert result.text == "text-of-page-1\n\ntext-of-page-2\n\ntext-of-page-3"
    assert result.scenario == "pdf"
    assert result.image_mode == "gundam"
    assert result.page_count == 3
    assert result.error is None


async def test_one_failing_page_does_not_sink_the_whole_pdf(fake_pages, monkeypatch):
    async def fake_run_ocr(scenario, parts):
        if parts[0] is fake_pages[1]:  # second page blows up
            raise RuntimeError("vLLM 400 on page 2")
        idx = fake_pages.index(parts[0]) + 1
        return f"text-of-page-{idx}"

    monkeypatch.setattr(main, "run_ocr", fake_run_ocr)

    result = await main._ocr_pdf(_FakeUpload(filename="doc.pdf"))

    # Surviving pages still produce text, in order.
    assert result.text == "text-of-page-1\n\ntext-of-page-3"
    # The failure is surfaced and points at the offending page.
    assert result.error is not None
    assert "page 2" in result.error
    assert result.page_count == 3

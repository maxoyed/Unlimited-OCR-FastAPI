# Unlimited-OCR-FastAPI

**English** | [简体中文](README.zh-CN.md)

A lightweight **FastAPI** server that turns **images and PDFs into text** using
Baidu's [Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) model.

The OCR model is **not** bundled or deployed by this service. You run the model
yourself with **[vLLM](https://github.com/vllm-project/vllm)** (which exposes an
OpenAI-compatible API), and this server talks to it. The vLLM URL, API key and
model name are supplied entirely through **environment variables**.

The request format follows the official Unlimited-OCR vLLM example exactly —
the literal `<image>` prompt prefix, `skip_special_tokens=false`, and the
DeepSeek-OCR no-repeat-ngram parameters (`ngram_size` / `window_size`) passed
via `vllm_xargs`.

> **The no-repeat-ngram logits processor must be registered on the vLLM
> server** (it is *not* sent per request). Launch vLLM with
> `--logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor`;
> without it long documents loop on `<|det|>` coordinate tokens.

## Fixed prompts per scenario

Prompts and sampling parameters are **hardcoded** (not user-configurable),
matching the official usage:

| Scenario          | Prompt                 | `image_mode` | `ngram_size` | `window_size` |
| ----------------- | ---------------------- | ------------ | ------------ | ------------- |
| Single image      | `document parsing.`    | `gundam`     | 35           | 128           |
| Multiple images   | `document parsing.`    | `gundam`     | 35           | 128           |
| PDF               | `document parsing.`    | `gundam`     | 35           | 128           |

Every page/image is parsed **individually** in `gundam` (crop) mode, and the
results are concatenated into one document. Sending all pages in a single
`Multi page parsing.` `base`-mode request lets the model degenerate into runaway
`<|det|>` coordinate repetition on a dense page and burn the whole token budget;
per-item parsing reads dense pages at full resolution and contains any failure
to its own page. The `image_mode` is reported back for information only and is
not client-selectable.

## Endpoints

| Method | Path         | Description                                                        |
| ------ | ------------ | ------------------------------------------------------------------ |
| GET    | `/health`    | Liveness + current model / vLLM URL.                               |
| POST   | `/ocr`       | Images become one document; each PDF its own document.             |
| POST   | `/ocr/image` | One image → single parse; many → one multi-page document.          |
| POST   | `/ocr/pdf`   | Each PDF → one multi-page document.                                |

Multipart form-data:

- `files`: one or more files (repeat the field for multiple files).

Interactive docs are at `/docs`.

### Response shape

```json
{
  "model": "baidu/Unlimited-OCR",
  "results": [
    {
      "name": "invoice.pdf",
      "scenario": "pdf",
      "image_mode": "gundam",
      "page_count": 2,
      "text": "…extracted text…",
      "error": null
    }
  ]
}
```

## Configuration

All settings come from environment variables (see [`.env.example`](.env.example)):

| Variable               | Default                     | Description                                          |
| ---------------------- | --------------------------- | ---------------------------------------------------- |
| `VLLM_BASE_URL`        | `http://localhost:8000`     | vLLM server root (`/v1/chat/completions` appended).  |
| `VLLM_API_KEY`         | *(empty)*                   | Bearer token; leave empty/`EMPTY` if no auth.        |
| `OCR_MODEL`            | `baidu/Unlimited-OCR`       | Served model name in vLLM.                            |
| `OCR_MAX_CONCURRENCY`  | `4`                         | Max concurrent OCR calls to vLLM.                    |
| `OCR_REQUEST_TIMEOUT`  | `1200`                      | Per-request timeout (seconds).                       |
| `OCR_MAX_TOKENS`       | `8192`                      | Max tokens generated per OCR call.                   |
| `PDF_DPI`              | `300`                       | Rasterisation DPI for PDF pages.                     |
| `MAX_FILE_SIZE_MB`     | `50`                        | Per-file size limit (0 = unlimited).                 |
| `MAX_FILES`            | `20`                        | Max files per request (0 = unlimited).               |

## Quick start (Docker Compose)

1. Deploy the model with vLLM somewhere reachable, e.g. via the dedicated
   release image (the architecture is not yet in a stable pip wheel):

   ```bash
   docker run --rm --gpus all --network host --ipc host \
     vllm/vllm-openai:unlimited-ocr \
     baidu/Unlimited-OCR \
     --trust-remote-code \
     --logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor \
     --no-enable-prefix-caching \
     --mm-processor-cache-gb 0
   ```

2. Point this service at it and start:

   ```bash
   cp api/.env.example .env   # edit VLLM_BASE_URL / VLLM_API_KEY / OCR_MODEL
   docker compose up --build
   ```

   By default it targets `http://host.docker.internal:8000` to reach a vLLM
   server running on the host machine.

3. The API is now on `http://localhost:8000` (docs at `/docs`).

## Quick start (local, without Docker)

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export VLLM_BASE_URL=http://localhost:8000
export OCR_MODEL=baidu/Unlimited-OCR
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Web demo (frontend)

A standalone browser demo lives in [`web/`](web/): drag-and-drop images / PDFs
and view the recognised markdown. Built with **Vite · React · TypeScript ·
TailwindCSS v4 · shadcn/ui · lucide-react**.

![Web demo](web/docs/screenshot-result.png)

Features:

- Drag-and-drop / click upload with client-side validation mirroring the
  backend limits (≤ 20 files, ≤ 50 MB each).
- Calls the unified `POST /ocr` endpoint and faithfully reflects its semantics
  (multiple images → one multi-page document, each PDF its own).
- Results render as markdown (headings, tables, lists). Grounding tokens
  (`<|ref|>` / `<|det|>`) are cleaned by default, with a **raw / cleaned**
  toggle and a copy button.
- Live backend health badge and light / dark theme.

```bash
cd web
pnpm install
pnpm dev        # http://localhost:5173  (expects the API on :8000)
```

The backend must allow the frontend origin via CORS (`CORS_ALLOW_ORIGINS`,
default `*`). See [`web/README.md`](web/README.md) for details.

## Usage examples

Single image (gundam):

```bash
curl -X POST http://localhost:8000/ocr/image -F "files=@page.jpg"
```

Multiple images (one multi-page document):

```bash
curl -X POST http://localhost:8000/ocr/image \
  -F "files=@page1.png" -F "files=@page2.png"
```

PDF(s):

```bash
curl -X POST http://localhost:8000/ocr/pdf -F "files=@document.pdf"
```

## Notes

- This service performs **no model deployment**; it only orchestrates uploads,
  PDF rasterisation, and calls to your vLLM endpoint using the official
  Unlimited-OCR request format.
- The no-repeat-ngram logits processor is registered on the vLLM server, so it
  is **not** sent per request — this service needs no sglang/torch dependency.
- Requests are streamed from vLLM internally and aggregated into the final text
  returned by the API.

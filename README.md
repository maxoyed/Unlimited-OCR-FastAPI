# Unlimited-OCR-FastAPI

A lightweight **FastAPI** server that turns **images and PDFs into text** using
Baidu's [Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) model.

The OCR model is **not** bundled or deployed by this service. You run the model
yourself with **[sglang](https://github.com/sgl-project/sglang)** (which exposes
an OpenAI-compatible API), and this server talks to it. The sglang URL and API
key are supplied entirely through **environment variables**.

```
┌──────────────┐   multipart upload    ┌──────────────────┐   OpenAI API    ┌────────────┐
│  client /    │ ────────────────────▶ │  FastAPI (this)  │ ──────────────▶ │  sglang +  │
│  curl / SDK  │ ◀──────────────────── │  image/PDF → png │ ◀────────────── │ Unlimited- │
└──────────────┘    JSON text result   └──────────────────┘   chat/completion│    OCR      │
                                                                              └────────────┘
```

## Features

- Upload **single or multiple** files in one request.
- Supports **images** (`png`, `jpg`, `jpeg`, `webp`, `bmp`, `tiff`, `gif`) and **PDFs**.
- PDFs are rasterised page-by-page (PyMuPDF) and each page is OCR'd.
- Pages and multiple files are processed **concurrently** (bounded by a configurable limit).
- Per-page results plus a concatenated full-text field.
- Configurable model name, OCR prompt, and limits via env vars.
- **Docker Compose** ready.

## Endpoints

| Method | Path         | Description                                  |
| ------ | ------------ | -------------------------------------------- |
| GET    | `/health`    | Liveness + current model / sglang URL.       |
| POST   | `/ocr`       | OCR any mix of images **and** PDFs.          |
| POST   | `/ocr/image` | Same as `/ocr`, intended for images.         |
| POST   | `/ocr/pdf`   | Same as `/ocr`, intended for PDFs.           |

All POST endpoints accept multipart form-data:

- `files`: one or more files (repeat the field for multiple files).
- `prompt` *(optional)*: override the default OCR prompt for this request.

Interactive docs are available at `/docs` once the server is running.

### Response shape

```json
{
  "model": "baidu/Unlimited-OCR",
  "results": [
    {
      "filename": "invoice.pdf",
      "type": "pdf",
      "page_count": 2,
      "text": "page one text\n\npage two text",
      "pages": [
        { "page": 1, "text": "page one text", "error": null },
        { "page": 2, "text": "page two text", "error": null }
      ],
      "error": null
    }
  ]
}
```

## Configuration

All settings come from environment variables (see [`.env.example`](.env.example)):

| Variable               | Default                                           | Description                                              |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------------- |
| `SGLANG_BASE_URL`      | `http://localhost:30000/v1`                       | sglang OpenAI-compatible base URL (**include `/v1`**).   |
| `SGLANG_API_KEY`       | `EMPTY`                                            | API key for sglang (`EMPTY` if the server has no auth).  |
| `OCR_MODEL`            | `baidu/Unlimited-OCR`                             | Served model name as registered in sglang.              |
| `OCR_PROMPT`           | `OCR this image. Return all text content faithfully.` | Default instruction sent with each image.          |
| `OCR_MAX_TOKENS`       | `8192`                                             | Max output tokens per page.                             |
| `OCR_TEMPERATURE`      | `0.0`                                              | Sampling temperature.                                   |
| `OCR_MAX_CONCURRENCY`  | `8`                                                | Max concurrent requests to sglang.                      |
| `OCR_REQUEST_TIMEOUT`  | `300`                                              | Per-request timeout (seconds).                          |
| `PDF_DPI`              | `200`                                              | Rasterisation DPI for PDF pages.                        |
| `MAX_FILE_SIZE_MB`     | `50`                                               | Per-file size limit (0 = unlimited).                    |
| `MAX_FILES`            | `20`                                               | Max files per request (0 = unlimited).                  |

## Quick start (Docker Compose)

1. Deploy the model with sglang somewhere reachable, for example:

   ```bash
   python -m sglang.launch_server \
     --model-path baidu/Unlimited-OCR \
     --host 0.0.0.0 --port 30000
   ```

2. Point this service at it and start:

   ```bash
   cp .env.example .env       # then edit SGLANG_BASE_URL / SGLANG_API_KEY / OCR_MODEL
   docker compose up --build
   ```

   The compose file reads these values from your shell/`.env`. By default it
   targets `http://host.docker.internal:30000/v1` so it can reach an sglang
   server running on the host machine.

3. The API is now on `http://localhost:8000` (docs at `/docs`).

## Quick start (local, without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SGLANG_BASE_URL=http://localhost:30000/v1
export SGLANG_API_KEY=EMPTY
export OCR_MODEL=baidu/Unlimited-OCR
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage examples

Single image:

```bash
curl -X POST http://localhost:8000/ocr \
  -F "files=@page1.png"
```

Multiple images + a PDF, with a custom prompt:

```bash
curl -X POST http://localhost:8000/ocr \
  -F "files=@page1.png" \
  -F "files=@page2.jpg" \
  -F "files=@document.pdf" \
  -F "prompt=Extract the text and preserve the layout as markdown."
```

Python:

```python
import requests

files = [
    ("files", ("a.png", open("a.png", "rb"), "image/png")),
    ("files", ("doc.pdf", open("doc.pdf", "rb"), "application/pdf")),
]
resp = requests.post("http://localhost:8000/ocr", files=files)
resp.raise_for_status()
for r in resp.json()["results"]:
    print(r["filename"], "->", r["text"][:200])
```

## Notes

- This service performs **no model deployment**; it only orchestrates uploads,
  PDF rasterisation, and calls to your sglang endpoint over the OpenAI-compatible
  API. Swap `OCR_MODEL` / `OCR_PROMPT` to use a different served model or task.
- If a single page fails, its error is reported in that page's `error` field
  while other pages/files still succeed (HTTP 200). File-level failures (e.g. a
  corrupt PDF) are reported in the file's `error` field.

# Unlimited-OCR-FastAPI

A lightweight **FastAPI** server that turns **images and PDFs into text** using
Baidu's [Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) model.

The OCR model is **not** bundled or deployed by this service. You run the model
yourself with **[sglang](https://github.com/sgl-project/sglang)** (which exposes
an OpenAI-compatible API), and this server talks to it. The sglang URL, API key
and model name are supplied entirely through **environment variables**.

The request format follows the official Unlimited-OCR sglang example exactly —
including `skip_special_tokens=false`, the `images_config.image_mode`, and the
DeepSeek-OCR no-repeat-ngram `custom_logit_processor` / `custom_params`.

## Fixed prompts per scenario

Prompts and sampling parameters are **hardcoded** (not user-configurable),
matching the official usage:

| Scenario          | Prompt                 | `image_mode`      | `ngram_size` | `window_size` |
| ----------------- | ---------------------- | ----------------- | ------------ | ------------- |
| Single image      | `document parsing.`    | `gundam` (or `base`) | 35        | 128           |
| Multiple images   | `Multi page parsing.`  | `base`            | 35           | 1024          |
| PDF               | `Multi page parsing.`  | `base`            | 35           | 1024          |

A single image supports either `gundam` (default) or `base`. Multiple images and
PDFs always use `base`.

### About the `custom_logit_processor`

The official client sends `DeepseekOCRNoRepeatNGramLogitProcessor.to_str()`.
Since that class is importable on the sglang server, `to_str()` serialises it
**by reference** — the blob only encodes the import path, which the server
resolves to its real implementation. We embed that exact serialized string in
[`app/logit_processor.py`](app/logit_processor.py) so this service needs **no
sglang/torch dependency**. Regenerate it with
[`scripts/gen_logit_processor.py`](scripts/gen_logit_processor.py) if needed.

## Endpoints

| Method | Path         | Description                                                        |
| ------ | ------------ | ------------------------------------------------------------------ |
| GET    | `/health`    | Liveness + current model / sglang URL.                             |
| POST   | `/ocr`       | Images become one document; each PDF its own document.             |
| POST   | `/ocr/image` | One image → single parse; many → one multi-page document.          |
| POST   | `/ocr/pdf`   | Each PDF → one multi-page document.                                |

Multipart form-data:

- `files`: one or more files (repeat the field for multiple files).
- `image_mode` *(optional, single image only)*: `gundam` (default) or `base`.

Interactive docs are at `/docs`.

### Response shape

```json
{
  "model": "Unlimited-OCR",
  "results": [
    {
      "name": "invoice.pdf",
      "scenario": "pdf",
      "image_mode": "base",
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
| `SGLANG_BASE_URL`      | `http://localhost:30000`    | sglang server root (`/v1/chat/completions` appended).|
| `SGLANG_API_KEY`       | *(empty)*                   | Bearer token; leave empty/`EMPTY` if no auth.        |
| `OCR_MODEL`            | `Unlimited-OCR`             | Served model name in sglang.                         |
| `OCR_MAX_CONCURRENCY`  | `4`                         | Max concurrent OCR calls to sglang.                  |
| `OCR_REQUEST_TIMEOUT`  | `1200`                      | Per-request timeout (seconds).                       |
| `PDF_DPI`              | `300`                       | Rasterisation DPI for PDF pages.                     |
| `MAX_FILE_SIZE_MB`     | `50`                        | Per-file size limit (0 = unlimited).                 |
| `MAX_FILES`            | `20`                        | Max files per request (0 = unlimited).               |

## Quick start (Docker Compose)

1. Deploy the model with sglang somewhere reachable, e.g.:

   ```bash
   python -m sglang.launch_server \
     --model-path baidu/Unlimited-OCR \
     --served-model-name Unlimited-OCR \
     --host 0.0.0.0 --port 30000
   ```

2. Point this service at it and start:

   ```bash
   cp .env.example .env       # edit SGLANG_BASE_URL / SGLANG_API_KEY / OCR_MODEL
   docker compose up --build
   ```

   By default it targets `http://host.docker.internal:30000` to reach an sglang
   server running on the host machine.

3. The API is now on `http://localhost:8000` (docs at `/docs`).

## Quick start (local, without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SGLANG_BASE_URL=http://localhost:30000
export OCR_MODEL=Unlimited-OCR
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage examples

Single image (gundam):

```bash
curl -X POST http://localhost:8000/ocr/image -F "files=@page.jpg"
```

Single image, base mode:

```bash
curl -X POST http://localhost:8000/ocr/image \
  -F "files=@page.jpg" -F "image_mode=base"
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
  PDF rasterisation, and calls to your sglang endpoint using the official
  Unlimited-OCR request format.
- Requests are streamed from sglang internally and aggregated into the final
  text returned by the API.

# Unlimited-OCR Web Demo

A frontend demo for the [Unlimited-OCR FastAPI](../README.md) service. Upload
single / multiple images or PDF files, send them to the API, and view the
recognised results as rendered markdown.

![Web demo](docs/screenshot-result.png)

## Stack

pnpm · Vite · React 19 · TypeScript · TailwindCSS v4 · shadcn/ui · lucide-react
· react-markdown.

## Features

- Drag-and-drop or click to select images / PDFs, with client-side validation
  mirroring the backend limits (≤ 20 files, ≤ 50 MB each).
- Calls the unified `POST /ocr` endpoint, which combines multiple images into
  one multi-page document and treats each PDF as its own document.
- Results render as markdown (headings, tables, lists). Grounding tokens
  (`<|ref|>` / `<|det|>`) are cleaned by default, with a **原文 / 清洗后**
  toggle and a copy button.
- Live backend health badge, light / dark theme.

## Configuration

| Variable            | Default                 | Description                       |
| ------------------- | ----------------------- | --------------------------------- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend.  |

Copy `.env.example` to `.env` to override.

> The backend must allow this origin via CORS. The FastAPI service reads
> `CORS_ALLOW_ORIGINS` (default `*`).

## Develop

```bash
pnpm install
pnpm dev        # http://localhost:5173
```

## Other scripts

```bash
pnpm build      # type-check + production build to dist/
pnpm preview    # serve the production build
pnpm test       # run unit tests (clean / validate)
pnpm lint       # eslint
```

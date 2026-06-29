# OCR Web Demo — Design

Date: 2026-06-29

## Goal

A standalone frontend that demonstrates the Unlimited-OCR FastAPI service:
upload single / multiple images and PDF files, send them to the API, and
display the recognised results.

## Tech Stack

pnpm · Vite · React 19 · TypeScript · TailwindCSS v4 (`@tailwindcss/vite`) ·
shadcn/ui (new-york) · lucide-react · react-markdown + remark-gfm · Vitest.

## Architecture

```
Unlimited-OCR-FastAPI/
├── app/    # existing backend — only adds CORS
└── web/    # new standalone Vite + React + TS frontend
```

### Backend change (minimal)

Add `CORSMiddleware` to `app/main.py`. Allowed origins come from a new env var
`CORS_ALLOW_ORIGINS` (comma-separated, default `*`), declared in `config.py`.
No credentials are used, so `*` is acceptable for a demo. This is the **only**
backend change.

### Frontend modules

| File | Responsibility |
| ---- | -------------- |
| `web/src/lib/api.ts` | Typed API client for `/ocr` and `/health`; types mirror backend `DocumentResult` / `OCRResponse`. Base URL from `VITE_API_BASE_URL` (default `http://localhost:8000`). |
| `web/src/lib/clean.ts` | Pure function: unwrap `<\|ref\|>…<\|/ref\|>`, drop `<\|det\|>…<\|/det\|>` coordinate boxes → clean markdown. |
| `web/src/lib/validate.ts` | Pure function: client-side validation of file type (image/pdf), count (≤20), size (≤50 MB), mirroring backend limits. |
| `web/src/components/UploadZone.tsx` | Drag-and-drop + click-to-select. |
| `web/src/components/FileList.tsx` | Selected files: type badge, image thumbnail, remove. |
| `web/src/components/ResultCard.tsx` | One document result: markdown render, raw/clean toggle, copy, error state. |
| `web/src/components/HealthBadge.tsx` | Backend `/health` status indicator. |
| `web/src/App.tsx` | Page composition + state (files, loading, results, error). |

## Data Flow

1. User drags / selects files → soft client-side validation.
2. Click "识别" → multipart `POST /ocr` (the unified endpoint handles mixed
   images + PDFs in one request).
3. Backend returns `{ model, results: DocumentResult[] }`.
4. Each `DocumentResult` renders as a card: grounding tokens cleaned and
   rendered as markdown by default, with a raw/clean toggle and a copy button.
5. Loading: skeletons. Failure: error banner.

### Faithful API semantics

The demo reflects `/ocr` behaviour exactly, no extra modes:

- Multiple images → combined into **one** multi-page document
  ("Multi page parsing"). The result `name` is e.g. `3 images: a.png, b.png`.
- Each PDF → its own document.

A short hint in the UI explains this so the combine behaviour is not surprising.

## Visual Design

Single-column focused layout: header (title + health badge + light/dark
toggle), prominent upload zone, file chips, results section. Restrained accent
colour (deep indigo) over default zinc, Inter body + monospace for raw text,
light/dark mode. Avoid a templated default-shadcn look.

## Testing

Pure logic (`clean.ts`, `validate.ts`) covered with Vitest. UI interactions are
not heavily tested — this is a demo app (YAGNI).

## Out of Scope

- Per-image separate recognition (no `/ocr/image`-per-file mode).
- Authentication, persistence, history.
- Backend serving the built frontend (frontend stays standalone).

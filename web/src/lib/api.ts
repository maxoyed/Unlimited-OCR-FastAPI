/**
 * Typed client for the Unlimited-OCR FastAPI backend.
 *
 * Types mirror the backend Pydantic models in ``app/schemas.py``. The base URL
 * comes from ``VITE_API_BASE_URL`` (default ``http://localhost:8000``); the
 * frontend appends ``/ocr`` and ``/health``.
 */

/** One recognised document — mirrors backend ``DocumentResult``. */
export interface DocumentResult {
  /** Source filename(s) for this document. */
  name: string
  /** OCR scenario: 'single_image', 'multi_image', or 'pdf'. */
  scenario: string
  /** Image mode used per page/image (always 'gundam'). */
  image_mode: string
  /** Number of pages/images parsed. */
  page_count: number
  /** Extracted text for the whole document. */
  text: string
  /** Error message if this document failed. */
  error?: string | null
}

/** Response of ``POST /ocr`` — mirrors backend ``OCRResponse``. */
export interface OCRResponse {
  model: string
  results: DocumentResult[]
}

/** Response of ``GET /health`` — mirrors backend ``HealthResponse``. */
export interface HealthResponse {
  status: string
  model: string
  vllm_base_url: string
}

const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "")

/** Extract a human-readable message from a failed response. */
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    const detail = (body as { detail?: unknown })?.detail
    if (typeof detail === "string") return detail
    if (detail != null) return JSON.stringify(detail)
  } catch {
    /* body was not JSON — fall through */
  }
  return `HTTP ${res.status} ${res.statusText}`
}

/**
 * Send images and/or PDFs to the unified ``/ocr`` endpoint.
 *
 * Faithful to backend semantics: all images are combined into a single
 * multi-page document, while each PDF becomes its own document.
 */
export async function runOcr(files: File[]): Promise<OCRResponse> {
  const form = new FormData()
  for (const file of files) {
    form.append("files", file, file.name)
  }

  let res: Response
  try {
    res = await fetch(`${BASE_URL}/ocr`, { method: "POST", body: form })
  } catch (err) {
    throw new Error(
      `无法连接后端（${BASE_URL}）：${String((err as Error)?.message ?? err)}`
    )
  }

  if (!res.ok) {
    throw new Error(await errorMessage(res))
  }
  return (await res.json()) as OCRResponse
}

/** Query backend health / model status. */
export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`)
  if (!res.ok) {
    throw new Error(await errorMessage(res))
  }
  return (await res.json()) as HealthResponse
}

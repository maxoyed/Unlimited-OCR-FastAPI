/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Unlimited-OCR FastAPI backend (default http://localhost:8000). */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

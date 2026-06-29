/**
 * Client-side validation of the file selection, mirroring backend limits in
 * ``app/config.py`` (``MAX_FILES`` / ``MAX_FILE_SIZE_MB``) and the supported
 * file kinds in ``app/utils.py``. This is a soft pre-check for UX; the backend
 * remains the source of truth.
 */

export const MAX_FILES = 20
export const MAX_FILE_SIZE_MB = 50

export type FileKind = "image" | "pdf" | "unknown"

const IMAGE_EXTENSIONS = [
  "png",
  "jpg",
  "jpeg",
  "webp",
  "bmp",
  "tif",
  "tiff",
  "gif",
]

/** Classify a file as image, pdf, or unknown by MIME type then extension. */
export function fileKind(file: File): FileKind {
  const type = file.type.toLowerCase()
  if (type === "application/pdf") return "pdf"
  if (type.startsWith("image/")) return "image"

  const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
  if (ext === "pdf") return "pdf"
  if (IMAGE_EXTENSIONS.includes(ext)) return "image"
  return "unknown"
}

/**
 * Validate a file selection and return human-readable error messages
 * (empty array == valid).
 */
export function validateSelection(files: File[]): string[] {
  const errors: string[] = []
  if (files.length === 0) return errors

  if (files.length > MAX_FILES) {
    errors.push(`最多支持 ${MAX_FILES} 个文件，当前选择了 ${files.length} 个。`)
  }

  const limitBytes = MAX_FILE_SIZE_MB * 1024 * 1024
  const unsupported: string[] = []
  const tooLarge: string[] = []
  for (const file of files) {
    if (fileKind(file) === "unknown") {
      unsupported.push(file.name)
    }
    if (file.size > limitBytes) {
      tooLarge.push(file.name)
    }
  }

  if (unsupported.length > 0) {
    errors.push(
      `不支持的文件类型：${unsupported.join("、")}。请上传图片或 PDF。`
    )
  }
  if (tooLarge.length > 0) {
    errors.push(
      `以下文件超过 ${MAX_FILE_SIZE_MB} MB 限制：${tooLarge.join("、")}。`
    )
  }

  return errors
}

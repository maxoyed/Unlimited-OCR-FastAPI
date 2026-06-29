import { describe, expect, it } from "vitest"

import {
  MAX_FILES,
  MAX_FILE_SIZE_MB,
  fileKind,
  validateSelection,
} from "@/lib/validate"

/**
 * Build a minimal File-like object. We avoid allocating real bytes so that
 * size limits can be exercised cheaply; only the fields validate.ts reads
 * (name, type, size) are provided.
 */
function makeFile(
  name: string,
  opts: { type?: string; sizeMB?: number } = {}
): File {
  return {
    name,
    type: opts.type ?? "",
    size: Math.round((opts.sizeMB ?? 0.1) * 1024 * 1024),
  } as File
}

describe("fileKind", () => {
  it("detects images by MIME type", () => {
    expect(fileKind(makeFile("a", { type: "image/png" }))).toBe("image")
    expect(fileKind(makeFile("b", { type: "image/jpeg" }))).toBe("image")
  })

  it("detects pdf by MIME type", () => {
    expect(fileKind(makeFile("a", { type: "application/pdf" }))).toBe("pdf")
  })

  it("falls back to extension when MIME is missing", () => {
    expect(fileKind(makeFile("scan.PNG"))).toBe("image")
    expect(fileKind(makeFile("doc.PDF"))).toBe("pdf")
    expect(fileKind(makeFile("photo.tiff"))).toBe("image")
  })

  it("returns unknown for unsupported files", () => {
    expect(fileKind(makeFile("notes.txt"))).toBe("unknown")
    expect(fileKind(makeFile("archive.zip"))).toBe("unknown")
    expect(fileKind(makeFile("noextension"))).toBe("unknown")
  })
})

describe("validateSelection", () => {
  it("returns no errors for an empty selection", () => {
    expect(validateSelection([])).toEqual([])
  })

  it("accepts a valid mixed selection", () => {
    const files = [
      makeFile("a.png", { type: "image/png", sizeMB: 1 }),
      makeFile("b.pdf", { type: "application/pdf", sizeMB: 2 }),
    ]
    expect(validateSelection(files)).toEqual([])
  })

  it("flags too many files", () => {
    const files = Array.from({ length: MAX_FILES + 1 }, (_, i) =>
      makeFile(`f${i}.png`, { type: "image/png" })
    )
    const errors = validateSelection(files)
    expect(errors).toHaveLength(1)
    expect(errors[0]).toContain(String(MAX_FILES))
  })

  it("flags unsupported file types", () => {
    const errors = validateSelection([makeFile("notes.txt")])
    expect(errors.some((e) => e.includes("notes.txt"))).toBe(true)
  })

  it("flags oversized files", () => {
    const errors = validateSelection([
      makeFile("huge.png", { type: "image/png", sizeMB: MAX_FILE_SIZE_MB + 1 }),
    ])
    expect(errors.some((e) => e.includes("huge.png"))).toBe(true)
  })

  it("accumulates multiple independent errors", () => {
    const files = [
      makeFile("notes.txt"),
      makeFile("huge.png", { type: "image/png", sizeMB: MAX_FILE_SIZE_MB + 1 }),
    ]
    const errors = validateSelection(files)
    expect(errors).toHaveLength(2)
  })
})

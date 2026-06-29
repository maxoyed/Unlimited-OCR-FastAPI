import { useEffect, useMemo } from "react"
import { FileText, X } from "lucide-react"

import { fileKind } from "@/lib/validate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface FileListProps {
  files: File[]
  onRemove: (index: number) => void
  disabled?: boolean
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function FileList({ files, onRemove, disabled }: FileListProps) {
  const previews = useMemo(
    () =>
      files.map((f) =>
        fileKind(f) === "image" ? URL.createObjectURL(f) : null
      ),
    [files]
  )

  // Revoke the object URLs when the file list changes or the list unmounts.
  useEffect(() => {
    return () => {
      previews.forEach((u) => u && URL.revokeObjectURL(u))
    }
  }, [previews])

  if (files.length === 0) return null

  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {files.map((file, i) => {
        const kind = fileKind(file)
        const preview = previews[i]
        return (
          <li
            key={`${file.name}-${file.size}-${i}`}
            className="flex items-center gap-3 rounded-lg border bg-card p-2.5"
          >
            <div className="flex size-11 shrink-0 items-center justify-center overflow-hidden rounded-md bg-muted">
              {preview ? (
                <img
                  src={preview}
                  alt={file.name}
                  className="size-full object-cover"
                />
              ) : (
                <FileText className="size-5 text-muted-foreground" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={file.name}>
                {file.name}
              </p>
              <div className="mt-0.5 flex items-center gap-2">
                <Badge variant={kind === "pdf" ? "secondary" : "default"}>
                  {kind === "pdf" ? "PDF" : kind === "image" ? "图片" : "未知"}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatSize(file.size)}
                </span>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-8 shrink-0 text-muted-foreground hover:text-destructive"
              disabled={disabled}
              onClick={() => onRemove(i)}
              aria-label={`移除 ${file.name}`}
            >
              <X className="size-4" />
            </Button>
          </li>
        )
      })}
    </ul>
  )
}

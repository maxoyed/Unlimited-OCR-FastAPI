import { useRef, useState } from "react"
import { FileUp, ImageIcon, FileText } from "lucide-react"

import { cn } from "@/lib/utils"
import { MAX_FILES, MAX_FILE_SIZE_MB } from "@/lib/validate"

interface UploadZoneProps {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

const ACCEPT =
  "image/png,image/jpeg,image/webp,image/bmp,image/tiff,image/gif,application/pdf,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff,.gif,.pdf"

export function UploadZone({ onFiles, disabled }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const emit = (list: FileList | null) => {
    if (!list || list.length === 0) return
    onFiles(Array.from(list))
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if (!disabled && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        if (!disabled) emit(e.dataTransfer.files)
      }}
      className={cn(
        "group relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
        disabled
          ? "cursor-not-allowed opacity-60"
          : "cursor-pointer hover:border-primary/60 hover:bg-accent/40",
        dragging
          ? "border-primary bg-accent/60"
          : "border-input bg-card/40"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPT}
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          emit(e.target.files)
          e.target.value = ""
        }}
      />
      <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary transition-transform group-hover:scale-105">
        <FileUp className="size-6" />
      </div>
      <div className="space-y-1">
        <p className="text-base font-medium">
          拖拽文件到此，或<span className="text-primary"> 点击选择</span>
        </p>
        <p className="text-sm text-muted-foreground">
          支持图片与 PDF，最多 {MAX_FILES} 个，单个 ≤ {MAX_FILE_SIZE_MB} MB
        </p>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <ImageIcon className="size-3.5" /> PNG / JPG / WEBP …
        </span>
        <span className="inline-flex items-center gap-1">
          <FileText className="size-3.5" /> PDF
        </span>
      </div>
    </div>
  )
}

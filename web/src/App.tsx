import { useMemo, useState } from "react"
import {
  AlertCircle,
  Eraser,
  Info,
  Loader2,
  Moon,
  ScanText,
  Sparkles,
  Sun,
} from "lucide-react"

import { runOcr, type DocumentResult } from "@/lib/api"
import { validateSelection } from "@/lib/validate"
import { useTheme } from "@/hooks/useTheme"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { HealthBadge } from "@/components/HealthBadge"
import { UploadZone } from "@/components/UploadZone"
import { FileList } from "@/components/FileList"
import { ResultCard } from "@/components/ResultCard"

export default function App() {
  const { theme, toggle } = useTheme()
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<DocumentResult[] | null>(null)
  const [model, setModel] = useState<string>("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validationErrors = useMemo(() => validateSelection(files), [files])
  const canSubmit = files.length > 0 && validationErrors.length === 0 && !loading

  const addFiles = (incoming: File[]) => {
    setError(null)
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}:${f.size}`))
      const merged = [...prev]
      for (const f of incoming) {
        const key = `${f.name}:${f.size}`
        if (!seen.has(key)) {
          seen.add(key)
          merged.push(f)
        }
      }
      return merged
    })
  }

  const removeFile = (index: number) =>
    setFiles((prev) => prev.filter((_, i) => i !== index))

  const clearAll = () => {
    setFiles([])
    setResults(null)
    setModel("")
    setError(null)
  }

  const submit = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const res = await runOcr(files)
      setResults(res.results)
      setModel(res.model)
    } catch (err) {
      setError(String((err as Error)?.message ?? err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ScanText className="size-5" />
            </div>
            <div className="leading-tight">
              <h1 className="text-base font-semibold">Unlimited-OCR</h1>
              <p className="text-xs text-muted-foreground">文档识别演示</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <HealthBadge />
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              aria-label="切换明暗主题"
            >
              {theme === "dark" ? (
                <Sun className="size-4" />
              ) : (
                <Moon className="size-4" />
              )}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-5 px-4 py-6">
        <Card>
          <CardContent className="space-y-4 pt-5">
            <UploadZone onFiles={addFiles} disabled={loading} />

            <FileList files={files} onRemove={removeFile} disabled={loading} />

            {validationErrors.length > 0 && (
              <div className="space-y-1 rounded-lg border border-destructive/30 bg-destructive/8 p-3 text-sm text-destructive">
                {validationErrors.map((msg, i) => (
                  <p key={i} className="flex items-start gap-2">
                    <AlertCircle className="mt-0.5 size-4 shrink-0" />
                    <span>{msg}</span>
                  </p>
                ))}
              </div>
            )}

            {files.length > 1 && (
              <p className="flex items-start gap-2 rounded-lg bg-accent/50 p-3 text-xs text-accent-foreground">
                <Info className="mt-0.5 size-3.5 shrink-0" />
                <span>
                  多张图片会被合并为<strong>一个多页文档</strong>识别；每个 PDF
                  各自作为独立文档。此为 <code>/ocr</code> 接口的真实行为。
                </span>
              </p>
            )}

            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">
                已选 {files.length} 个文件
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={clearAll}
                  disabled={loading || files.length === 0}
                >
                  <Eraser className="size-4" />
                  清空
                </Button>
                <Button onClick={submit} disabled={!canSubmit}>
                  {loading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Sparkles className="size-4" />
                  )}
                  {loading ? "识别中…" : "开始识别"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/8 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <span className="break-words">请求失败：{error}</span>
          </div>
        )}

        {loading && (
          <div className="space-y-3">
            {Array.from({ length: Math.max(1, files.length) }).map((_, i) => (
              <div
                key={i}
                className="h-32 animate-pulse rounded-xl border bg-card"
              />
            ))}
          </div>
        )}

        {results && !loading && (
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-muted-foreground">
                识别结果 · {results.length} 个文档
              </h2>
              {model && (
                <span className="text-xs text-muted-foreground">{model}</span>
              )}
            </div>
            {results.map((r, i) => (
              <ResultCard key={i} result={r} index={i} />
            ))}
          </section>
        )}
      </main>

      <footer className="mx-auto max-w-3xl px-4 pb-8 pt-2 text-center text-xs text-muted-foreground">
        基于 Baidu Unlimited-OCR · 模型经 vLLM 部署
      </footer>
    </div>
  )
}

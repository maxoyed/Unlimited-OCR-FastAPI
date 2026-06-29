import { useMemo, useState } from "react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  AlertTriangle,
  Check,
  Copy,
  Code2,
  FileText,
  Layers,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { cleanGroundingTokens } from "@/lib/clean"
import type { DocumentResult } from "@/lib/api"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const MARKDOWN_CLASS = cn(
  "max-w-none text-sm leading-relaxed",
  "[&_h1]:mt-4 [&_h1]:mb-2 [&_h1]:text-xl [&_h1]:font-semibold",
  "[&_h2]:mt-4 [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold",
  "[&_h3]:mt-3 [&_h3]:mb-1.5 [&_h3]:text-base [&_h3]:font-semibold",
  "[&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5",
  "[&_li]:my-1 [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-2",
  "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.85em]",
  "[&_pre]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-muted [&_pre]:p-3",
  "[&_pre_code]:bg-transparent [&_pre_code]:p-0",
  "[&_blockquote]:border-l-2 [&_blockquote]:border-primary/40 [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground",
  "[&_table]:my-2 [&_table]:w-full [&_table]:border-collapse [&_table]:text-xs",
  "[&_th]:border [&_th]:bg-muted [&_th]:px-2 [&_th]:py-1 [&_th]:text-left",
  "[&_td]:border [&_td]:px-2 [&_td]:py-1",
  "[&_img]:my-2 [&_img]:max-w-full [&_img]:rounded-md"
)

interface ResultCardProps {
  result: DocumentResult
  index: number
}

export function ResultCard({ result, index }: ResultCardProps) {
  const [showRaw, setShowRaw] = useState(false)
  const [copied, setCopied] = useState(false)

  const cleaned = useMemo(
    () => cleanGroundingTokens(result.text),
    [result.text]
  )
  const display = showRaw ? result.text : cleaned
  const hasError = Boolean(result.error)
  const isEmpty = !hasError && cleaned.trim().length === 0

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(display)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard may be unavailable over http — ignore */
    }
  }

  return (
    <Card>
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <CardTitle
            className="flex min-w-0 items-center gap-2"
            title={result.name}
          >
            <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
              {index + 1}
            </span>
            <span className="truncate">{result.name}</span>
          </CardTitle>
          {!hasError && (
            <div className="flex shrink-0 items-center gap-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowRaw((v) => !v)}
                title="切换原文 / 清洗后视图"
              >
                <Code2 className="size-3.5" />
                {showRaw ? "清洗后" : "原文"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copy}
                title="复制当前文本"
              >
                {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                {copied ? "已复制" : "复制"}
              </Button>
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="secondary">
            <Layers className="size-3" />
            {result.scenario}
          </Badge>
          <Badge variant="outline">{result.image_mode}</Badge>
          <Badge variant="outline">
            <FileText className="size-3" />
            {result.page_count} 页
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {hasError ? (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/8 p-3 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span className="break-words">{result.error}</span>
          </div>
        ) : isEmpty ? (
          <p className="text-sm text-muted-foreground">（未识别到文本）</p>
        ) : showRaw ? (
          <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-muted p-3 font-mono text-xs leading-relaxed">
            {result.text}
          </pre>
        ) : (
          <div className={MARKDOWN_CLASS}>
            <Markdown remarkPlugins={[remarkGfm]}>{cleaned}</Markdown>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

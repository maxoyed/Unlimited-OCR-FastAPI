import { useEffect, useState } from "react"
import { CircleCheck, CircleX, Loader2 } from "lucide-react"

import { getHealth, type HealthResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string }

export function HealthBadge() {
  const [state, setState] = useState<State>({ kind: "loading" })

  useEffect(() => {
    let active = true
    getHealth()
      .then((data) => active && setState({ kind: "ok", data }))
      .catch(
        (err) =>
          active &&
          setState({ kind: "error", message: String(err?.message ?? err) })
      )
    return () => {
      active = false
    }
  }, [])

  if (state.kind === "loading") {
    return (
      <Badge variant="secondary" title="正在检查后端状态">
        <Loader2 className="size-3 animate-spin" />
        连接中
      </Badge>
    )
  }
  if (state.kind === "error") {
    return (
      <Badge variant="destructive" title={state.message}>
        <CircleX className="size-3" />
        后端不可达
      </Badge>
    )
  }
  return (
    <Badge variant="success" title={`模型：${state.data.model}`}>
      <CircleCheck className="size-3" />
      在线 · {state.data.model}
    </Badge>
  )
}

// ── Conversations ──────────────────────────────────────────────────────────

export type Conversation = {
  id: string
  title: string | null
  updated_at: string
}

// ── Messages ───────────────────────────────────────────────────────────────

export type Step =
  | { type: "thought"; text: string }
  | { type: "tool_call"; name: string; args: Record<string, unknown>; result: string }

export type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  steps?: Step[]
  pending?: boolean
  fresh?: boolean
}


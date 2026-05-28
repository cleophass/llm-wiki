"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { CornerDownLeft } from "lucide-react"
import { renderMarkdown } from "@/lib/renderMarkdown"
import type { Message, Step } from "@/lib/types"

const FLAVOR_MESSAGES = [
  "Exploration du wiki",
  "Lecture des sections",
  "Recoupement des informations",
  "Analyse des pages",
  "Recherche en cours",
  "Synthèse en cours",
]

// ── ChatPanel ─────────────────────────────────────────────────────────────────

export function ChatPanel({
  conversationId,
  initialMessages,
  onAddDocuments,
}: {
  conversationId: string
  initialMessages: Message[]
  onAddDocuments?: () => void
}) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const router = useRouter()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (loading || !input.trim()) return

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: input }
    const assistantId = crypto.randomUUID()
    const assistantMsg: Message = { id: assistantId, role: "assistant", content: "", pending: true }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    const sentInput = input
    setInput("")
    setLoading(true)

    try {
      const res = await fetch(`/api/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: sentInput }),
      })

      if (!res.ok) throw new Error("Erreur serveur")
      const data = await res.json()

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: data.content, steps: data.steps ?? [], pending: false, fresh: true }
            : m
        )
      )

      if (data.title) router.refresh()
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "Une erreur est survenue.", pending: false }
            : m
        )
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-canvas">
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-7">
        {onAddDocuments && (
          <div className="rounded-2xl border border-hairline bg-surface-card px-5 py-4">
            <p className="text-sm font-medium text-ink">Le wiki se construit ici</p>
            <p className="text-[12px] text-muted mt-1">
              Ajoute des documents, puis ouvre le wiki pour voir les pages générées.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={onAddDocuments}
                className="inline-flex items-center gap-2 rounded-full border border-hairline px-4 py-2 text-[12px] font-medium text-muted hover:text-ink hover:border-muted-soft transition-colors"
              >
                Ajouter un document
              </button>
              <Link
                href={`/conversations/${conversationId}/wiki`}
                className="inline-flex items-center gap-2 rounded-full border border-transparent px-4 py-2 text-[12px] font-medium text-muted hover:text-ink transition-colors"
              >
                Ouvrir le wiki →
              </Link>
            </div>
          </div>
        )}
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center pt-10">
            <p className="text-2xl font-medium text-ink">Commence par envoyer un message</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageRow key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 px-6 py-4 border-t border-hairline">
        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e as unknown as React.FormEvent)
                }
              }}
              placeholder="Envoie un message…"
              rows={1}
              disabled={loading}
              className="w-full resize-none overflow-hidden outline-none disabled:opacity-50 bg-canvas border border-[#d4d4d4] rounded-[14px] px-4 py-2.5 text-sm leading-[1.55] text-ink font-body pr-10 shadow-[0_1px_3px_rgba(0,0,0,0.06)] focus:border-[#b8b8b8] transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2.5 bottom-2 flex items-center justify-center w-6 h-6 text-muted hover:text-ink transition-colors disabled:opacity-25"
              title="Envoyer"
            >
              <CornerDownLeft size={15} strokeWidth={1.5} />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Message row ───────────────────────────────────────────────────────────────

function MessageRow({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[72%] px-4 py-2.5 bg-surface-card border border-hairline text-sm leading-[1.55] text-body"
          style={{ borderRadius: "12px 12px 4px 12px" }}
        >
          <span className="whitespace-pre-wrap">{message.content}</span>
        </div>
      </div>
    )
  }

  if (message.pending && !message.content) {
    return <ExploringIndicator />
  }

  if (!message.content) return null

  const steps = message.steps ?? []

  if (message.fresh) {
    return <AnimatedMessage content={message.content} steps={steps} />
  }

  return <StaticMessage content={message.content} steps={steps} />
}

// ── Exploring indicator ───────────────────────────────────────────────────────

function ExploringIndicator() {
  const [i, setI] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % FLAVOR_MESSAGES.length), 2200)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="flex items-center gap-2.5 max-w-[82%]">
      <div className="shrink-0 w-3 h-3 rounded-full border-2 border-muted-soft border-t-muted animate-spin" />
      <span className="text-[12px] text-muted transition-all">{FLAVOR_MESSAGES[i]}…</span>
    </div>
  )
}

// ── Static message ────────────────────────────────────────────────────────────

function StaticMessage({ content, steps }: { content: string; steps: Step[] }) {
  return (
    <div className="flex flex-col gap-2.5 max-w-[82%]">
      {steps.map((step, i) => {
        if (step.type === "thought") {
          return (
            <p key={i} className="text-[12px] italic text-muted leading-relaxed">
              {step.text}
            </p>
          )
        }
        return <ToolCallRow key={i} step={step} />
      })}
      <div className="text-sm leading-[1.65] text-body">{renderMarkdown(content)}</div>
    </div>
  )
}

// ── Animated message ──────────────────────────────────────────────────────────

function AnimatedMessage({ content, steps }: { content: string; steps: Step[] }) {
  const totalItems = steps.length + 1
  const [idx, setIdx] = useState(0)
  const [chars, setChars] = useState(0)

  const isAnswerPhase = idx >= steps.length
  const isDone = idx >= totalItems

  useEffect(() => {
    if (isDone) return

    // tool_call : avance instantanément
    if (!isAnswerPhase && steps[idx].type === "tool_call") {
      const t = setTimeout(() => {
        setIdx((i) => i + 1)
        setChars(0)
      }, 60)
      return () => clearTimeout(t)
    }

    const text = isAnswerPhase
      ? content
      : (steps[idx] as Extract<Step, { type: "thought" }>).text

    if (chars >= text.length) {
      if (idx < totalItems - 1) {
        const t = setTimeout(() => {
          setIdx((i) => i + 1)
          setChars(0)
        }, 200)
        return () => clearTimeout(t)
      }
      return
    }

    // avance mot par mot
    const t = setTimeout(() => {
      setChars((c) => {
        const next = text.indexOf(" ", c + 1)
        return next === -1 ? text.length : next + 1
      })
    }, 28)
    return () => clearTimeout(t)
  }, [idx, chars, isDone, isAnswerPhase])

  return (
    <div className="flex flex-col gap-2.5 max-w-[82%]">
      {steps.map((step, i) => {
        if (i > idx) return null

        if (step.type === "thought") {
          const text = i === idx ? step.text.slice(0, chars) : step.text
          return (
            <p key={i} className="text-[12px] italic text-muted leading-relaxed">
              {text}
            </p>
          )
        }

        return <ToolCallRow key={i} step={step} />
      })}

      {isAnswerPhase && (
        <div className="text-sm leading-[1.65] text-body">
          {isDone ? (
            renderMarkdown(content)
          ) : (
            <span className="whitespace-pre-wrap">{content.slice(0, chars)}</span>
          )}
        </div>
      )}
    </div>
  )
}

// ── Tool call row ─────────────────────────────────────────────────────────────

function ToolCallRow({ step }: { step: Extract<Step, { type: "tool_call" }> }) {
  const [open, setOpen] = useState(false)

  const argsStr = Object.entries(step.args)
    .map(([k, v]) => `${k}: ${String(v)}`)
    .join("  ")

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-baseline gap-2 text-left hover:opacity-70 transition-opacity"
      >
        <span className="text-[12px] font-mono text-muted">{step.name}</span>
        {argsStr && <span className="text-[12px] text-muted-soft">{argsStr}</span>}
        <span className="text-[10px] text-muted-soft">{open ? "▲" : "▼"}</span>
      </button>
      {open && step.result && (
        <pre className="mt-1 pl-2 text-[11px] text-muted-soft leading-relaxed whitespace-pre-wrap border-l border-hairline">
          {step.result}
        </pre>
      )}
    </div>
  )
}


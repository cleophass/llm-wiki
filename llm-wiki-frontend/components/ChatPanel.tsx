"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { CornerDownLeft } from "lucide-react"
import { renderMarkdown } from "@/lib/renderMarkdown"
import type { Message } from "@/lib/types"

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
          m.id === assistantId ? { ...m, content: data.content, pending: false } : m
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
      {/* Messages */}
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
            <div className="text-center space-y-3">
              <p className="text-2xl font-medium text-ink">
                Commence par envoyer un message
              </p>
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <MessageRow key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
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

// ── Message row ──────────────────────────────────────────────────────────────

function MessageRow({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[72%] px-4 py-2.5 bg-surface-card border border-hairline text-sm leading-[1.55] text-body" style={{ borderRadius: "12px 12px 4px 12px" }}>
          <span className="whitespace-pre-wrap">{message.content}</span>
        </div>
      </div>
    )
  }

  if (message.pending && !message.content) {
    return (
      <div className="flex flex-col gap-2.5 max-w-[82%]">
        <div className="text-sm leading-[1.65] text-body">
          <span className="animate-pulse text-muted-soft">···</span>
        </div>
      </div>
    )
  }

  if (!message.content) return null

  return (
    <div className="flex flex-col gap-2.5 max-w-[82%]">
      <div className="text-sm leading-[1.65] text-body">
        {renderMarkdown(message.content)}
      </div>
    </div>
  )
}

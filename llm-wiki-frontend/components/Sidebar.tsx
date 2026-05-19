"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useState } from "react"
import type { Conversation } from "@/lib/types"

export function Sidebar({ conversations }: { conversations: Conversation[] }) {
  const pathname = usePathname()
  const router = useRouter()
  const [creating, setCreating] = useState(false)

  const activeId = pathname.match(/\/conversations\/([^/]+)/)?.[1]

  async function handleNew() {
    setCreating(true)
    try {
      const res = await fetch("/api/conversations", { method: "POST" })
      const data = await res.json()
      router.push(`/conversations/${data.id}`)
      router.refresh()
    } finally {
      setCreating(false)
    }
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col h-full bg-canvas border-r border-hairline">
      {/* Wordmark */}
      <div className="px-5 pt-6 pb-4 flex items-center justify-between">
        <span className="text-[15px] font-semibold text-ink tracking-tight">LLM Wiki</span>
        <button
          onClick={handleNew}
          disabled={creating}
          title="Nouvelle conversation"
          className="flex items-center justify-center w-7 h-7 rounded-full border border-hairline bg-canvas text-muted transition-opacity disabled:opacity-40 hover:text-ink"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
      </div>

      <div className="h-px bg-hairline-soft mb-2" />

      <div className="px-3 pb-3">
        <p className="px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-soft mb-2">
          Accès rapide
        </p>
        {activeId ? (
          <Link
            href={`/conversations/${activeId}/wiki`}
            className="flex items-center justify-between rounded-lg border border-hairline px-3 py-2 text-[12px] text-ink bg-surface-soft hover:border-muted-soft transition-colors"
          >
            Wiki du dossier
            <span className="text-muted">→</span>
          </Link>
        ) : (
          <p className="px-2 text-[12px] text-muted-soft">
            Sélectionne une conversation pour accéder au wiki.
          </p>
        )}
      </div>

      {/* Conversation list */}
      <nav className="flex-1 overflow-y-auto px-2 py-1 space-y-0.5">
        {conversations.length === 0 && (
          <p className="px-3 py-2 text-xs text-muted-soft">Aucune conversation</p>
        )}
        {conversations.map((conv) => {
          const isActive = conv.id === activeId
          return (
            <Link
              key={conv.id}
              href={`/conversations/${conv.id}`}
              className="block rounded-lg px-3 py-2 text-[13px] truncate transition-colors"
              style={{
                background: isActive ? "var(--color-surface-card)" : "transparent",
                color: isActive ? "var(--color-ink)" : "var(--color-muted)",
                fontWeight: isActive ? 500 : 400,
              }}
            >
              {conv.title ?? "Nouvelle conversation"}
            </Link>
          )
        })}
      </nav>

    </aside>
  )
}

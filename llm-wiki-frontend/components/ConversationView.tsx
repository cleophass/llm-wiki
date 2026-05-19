"use client"

import Link from "next/link"
import { useState } from "react"
import { ChatPanel } from "@/components/ChatPanel"
import { WikiPanel } from "@/components/WikiPanel"
import type { Message } from "@/lib/types"

type Tab = "chat" | "documents"

const TABS: { id: Tab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "documents", label: "Documents" },
]

export function ConversationView({
  conversationId,
  initialMessages,
}: {
  conversationId: string
  initialMessages: Message[]
}) {
  const [tab, setTab] = useState<Tab>("chat")

  return (
    <div className="flex flex-col h-full">
      <div className="shrink-0 flex items-center justify-between gap-4 px-6 border-b border-hairline">
        <div className="flex gap-0">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={[
                "relative px-4 py-3 text-[13px] font-medium transition-colors",
                tab === t.id ? "text-ink" : "text-muted hover:text-ink",
              ].join(" ")}
            >
              {t.label}
              {tab === t.id && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-ink rounded-t-full" />
              )}
            </button>
          ))}
        </div>
        <Link
          href={`/conversations/${conversationId}/wiki`}
          className="text-[12px] font-medium text-muted hover:text-ink transition-colors"
        >
          Ouvrir le wiki →
        </Link>
      </div>

      <div className="flex-1 min-h-0">
        <div className={tab === "chat" ? "h-full" : "hidden"}>
          <ChatPanel
            conversationId={conversationId}
            initialMessages={initialMessages}
            onAddDocuments={() => setTab("documents")}
          />
        </div>
        <div className={tab === "documents" ? "h-full overflow-y-auto" : "hidden"}>
          <WikiPanel conversationId={conversationId} />
        </div>
      </div>
    </div>
  )
}

"use client"

import { ChatPanel } from "@/components/ChatPanel"
import type { Message } from "@/lib/types"

export function ConversationView({
  conversationId,
  initialMessages,
}: {
  conversationId: string
  initialMessages: Message[]
}) {
  return <ChatPanel conversationId={conversationId} initialMessages={initialMessages} />
}

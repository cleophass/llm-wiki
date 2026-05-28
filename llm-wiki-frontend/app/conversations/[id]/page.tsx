import { notFound } from "next/navigation"
import { ConversationView } from "@/components/ConversationView"
import type { Message, Step } from "@/lib/types"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

async function getInitialMessages(id: string): Promise<Message[] | null> {
  try {
    const res = await fetch(`${BACKEND}/conversations/${id}/messages`, { cache: "no-store" })
    if (res.status === 404) return null
    if (!res.ok) return []
    const raw: Array<{ role: string; content: string; steps?: Step[] }> = await res.json()
    return raw.map((m, i) => ({
      id: `hist-${i}`,
      role: m.role as "user" | "assistant",
      content: m.content,
      steps: m.steps,
    }))
  } catch {
    return []
  }
}

export default async function ConversationPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const messages = await getInitialMessages(id)
  if (messages === null) notFound()

  return <ConversationView conversationId={id} initialMessages={messages} />
}

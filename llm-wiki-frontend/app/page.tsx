import { redirect } from "next/navigation"
import { getConversations } from "@/lib/api"

export default async function HomePage() {
  const conversations = await getConversations()

  if (conversations.length > 0) {
    redirect(`/conversations/${conversations[0].id}`)
  }

  return (
    <div
      className="flex h-full items-center justify-center"
      style={{ background: "var(--color-canvas)" }}
    >
      <div className="text-center space-y-3">
        <p
          style={{
            fontFamily: "var(--font-display), serif",
            fontSize: 28,
            fontWeight: 400,
            color: "var(--color-ink)",
            letterSpacing: "-0.3px",
          }}
        >
          Aucune conversation
        </p>
        <p style={{ fontSize: 14, color: "var(--color-muted)" }}>
          Crée une nouvelle conversation dans la sidebar.
        </p>
      </div>
    </div>
  )
}

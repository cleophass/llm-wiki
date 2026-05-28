/**
 * Fonctions d'appel au backend — uniquement depuis les Server Components.
 * Les Client Components passent par les routes proxy /api/...
 */
import type { Conversation } from "./types"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

export async function getConversations(): Promise<Conversation[]> {
  try {
    const res = await fetch(`${BACKEND}/conversations`, { cache: "no-store" })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

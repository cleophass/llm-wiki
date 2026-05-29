import { notFound } from "next/navigation"
import Link from "next/link"
import { DiffView, type PageChange } from "@/components/DiffView"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

type IngestionEvent = {
  id: string
  timestamp: string
  files: string[]
  changes: PageChange[]
}

async function getEvent(id: string): Promise<IngestionEvent | null> {
  try {
    const res = await fetch(`${BACKEND}/wiki/history/${id}`, { cache: "no-store" })
    if (res.status === 404) return null
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default async function IngestionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const event = await getEvent(id)
  if (!event) notFound()

  const totalAdded = event.changes.reduce((n, c) => n + c.sections_added.length, 0)
  const totalModified = event.changes.reduce((n, c) => n + c.sections_modified.length, 0)
  const totalDeleted = event.changes.reduce((n, c) => n + c.sections_deleted.length, 0)

  return (
    <div className="h-full overflow-y-auto px-10 py-10 max-w-3xl mx-auto">
      <Link href="/wiki" className="text-[12px] text-muted hover:text-ink transition-colors mb-6 inline-block">
        ← Wiki
      </Link>

      <h1 className="text-[20px] font-semibold text-ink mb-1">
        {event.files.join(", ")}
      </h1>
      <p className="text-[13px] text-muted mb-2">{formatDate(event.timestamp)}</p>

      <div className="flex gap-3 text-[12px] font-medium mb-8">
        {totalAdded > 0 && <span className="text-green-500">+{totalAdded} ajoutée{totalAdded > 1 ? "s" : ""}</span>}
        {totalDeleted > 0 && <span className="text-red-500">−{totalDeleted} supprimée{totalDeleted > 1 ? "s" : ""}</span>}
        {event.changes.length === 0 && <span className="text-muted">aucun changement</span>}
      </div>

      <DiffView changes={event.changes} />
    </div>
  )
}

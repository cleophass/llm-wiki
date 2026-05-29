import Link from "next/link"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

type IngestionSummary = {
  id: string
  timestamp: string
  files: string[]
  pages_changed: number
  sections_added: number
  sections_modified: number
  sections_deleted: number
}

async function getHistory(): Promise<IngestionSummary[]> {
  try {
    const res = await fetch(`${BACKEND}/wiki/history`, { cache: "no-store" })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default async function HistoryPage() {
  const events = await getHistory()

  return (
    <div className="h-full overflow-y-auto px-10 py-10 max-w-3xl mx-auto">
      <h1 className="text-[22px] font-semibold text-ink mb-1">Historique des ingestions</h1>
      <p className="text-sm text-muted mb-8">
        {events.length} ingestion{events.length !== 1 ? "s" : ""}
      </p>

      {events.length === 0 && (
        <p className="text-sm text-muted">Aucune ingestion pour l'instant.</p>
      )}

      <div className="space-y-3">
        {events.map((e) => (
          <Link
            key={e.id}
            href={`/wiki/history/${e.id}`}
            className="block rounded-xl border border-hairline bg-surface-card px-5 py-4 hover:border-muted-soft transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-[13px] font-medium text-ink truncate">
                  {e.files.join(", ")}
                </p>
                <p className="text-[12px] text-muted mt-0.5">{formatDate(e.timestamp)}</p>
              </div>
              <div className="shrink-0 flex gap-2 text-[11px] font-medium mt-0.5">
                {e.sections_added > 0 && (
                  <span className="text-green-500">+{e.sections_added}</span>
                )}
                {e.sections_deleted > 0 && (
                  <span className="text-red-500">−{e.sections_deleted}</span>
                )}
                {e.pages_changed === 0 && (
                  <span className="text-muted">aucun changement</span>
                )}
              </div>
            </div>
            {e.pages_changed > 0 && (
              <p className="text-[11px] text-muted mt-2">
                {e.pages_changed} page{e.pages_changed !== 1 ? "s" : ""} modifiée{e.pages_changed !== 1 ? "s" : ""}
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}

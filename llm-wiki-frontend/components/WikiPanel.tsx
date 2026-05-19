"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"

type IngestionSummary = {
  id: string
  timestamp: string
  files: string[]
  pages_changed: number
  sections_added: number
  sections_modified: number
  sections_deleted: number
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

export function WikiPanel({ conversationId }: { conversationId: string }) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [ingesting, setIngesting] = useState(false)
  const [history, setHistory] = useState<IngestionSummary[]>([])

  async function loadHistory() {
    try {
      const res = await fetch("/api/wiki/history")
      if (res.ok) setHistory(await res.json())
    } catch {}
  }

  useEffect(() => { loadHistory() }, [])

  async function handleIngest(files: FileList | null) {
    if (!files || files.length === 0) return
    setIngesting(true)
    try {
      const formData = new FormData()
      Array.from(files).forEach((f) => formData.append("files", f))
      await fetch("/api/wiki/ingest", { method: "POST", body: formData })
      await loadHistory()
    } finally {
      setIngesting(false)
    }
  }

  return (
    <div className="px-8 py-8 max-w-2xl space-y-8">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.txt"
        className="hidden"
        onChange={(e) => {
          handleIngest(e.target.files)
          e.target.value = ""
        }}
      />

      <div className="rounded-2xl border border-hairline bg-surface-card px-5 py-4">
        <p className="text-sm font-medium text-ink">Ajoute des documents pour enrichir le wiki</p>
        <p className="text-[12px] text-muted mt-1">
          PDFs, images ou TXT : chaque ingestion met à jour les pages du wiki.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={ingesting}
            className="flex items-center gap-2 rounded-lg border border-hairline px-4 py-2.5 text-[13px] text-muted hover:text-ink hover:border-muted-soft transition-colors disabled:opacity-50"
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 7.5l-5.5 5.5a4 4 0 01-5.657-5.657l5.5-5.5a2.5 2.5 0 013.536 3.536l-5.507 5.507a1 1 0 01-1.414-1.414l5.5-5.5" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round"/>
            </svg>
            {ingesting ? "Traitement…" : "Ajouter un document"}
          </button>
          <Link
            href={`/conversations/${conversationId}/wiki`}
            className="flex items-center gap-2 rounded-lg border border-transparent px-4 py-2.5 text-[13px] text-muted hover:text-ink transition-colors"
          >
            Ouvrir le wiki →
          </Link>
        </div>
      </div>

      <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-soft mb-3">
        Ingestions
      </p>

      {history.length === 0 ? (
        <p className="text-[13px] text-muted">Aucune ingestion pour l'instant.</p>
      ) : (
        <div className="space-y-2">
          {history.map((e) => (
            <Link
              key={e.id}
              href={`/wiki/history/${e.id}`}
              className="block rounded-lg border border-hairline px-4 py-3 hover:bg-surface-soft transition-colors"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-[13px] font-medium text-ink truncate">
                  {e.files.join(", ")}
                </p>
                <div className="shrink-0 flex gap-2 text-[11px] font-semibold">
                  {e.sections_added > 0 && (
                    <span className="text-green-500">+{e.sections_added}</span>
                  )}
                  {e.sections_modified > 0 && (
                    <span className="text-yellow-500">~{e.sections_modified}</span>
                  )}
                  {e.sections_deleted > 0 && (
                    <span className="text-red-500">−{e.sections_deleted}</span>
                  )}
                  {e.pages_changed === 0 && (
                    <span className="text-muted-soft">∅</span>
                  )}
                </div>
              </div>
              <p className="text-[11px] text-muted mt-0.5">{formatDate(e.timestamp)}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

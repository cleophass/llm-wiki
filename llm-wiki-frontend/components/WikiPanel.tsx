"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"

type IngestionSummary = {
  id: string
  timestamp: string
  files: string[]
  pages_changed: number
  sections_added: number
  sections_modified: number
  sections_deleted: number
}

const FLAVOR_MESSAGES = [
  "Lecture du document",
  "Extraction des informations",
  "Mise à jour du wiki",
  "Analyse en cours",
  "Traitement des pages",
  "Organisation du contenu",
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

// ── Carte "En cours" ─────────────────────────────────────────────────────────

function PendingCard({ fileNames }: { fileNames: string[] }) {
  const [i, setI] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % FLAVOR_MESSAGES.length), 2200)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="rounded-lg border border-hairline px-4 py-3 opacity-80">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[13px] font-medium text-ink truncate">{fileNames.join(", ")}</p>
        <div className="shrink-0 w-3 h-3 rounded-full border-2 border-muted-soft border-t-muted animate-spin" />
      </div>
      <p className="text-[11px] text-muted mt-0.5">{FLAVOR_MESSAGES[i]}…</p>
    </div>
  )
}

// ── Modal drag & drop ─────────────────────────────────────────────────────────

function UploadModal({
  onClose,
  onSubmit,
}: {
  onClose: () => void
  onSubmit: (files: File[]) => void
}) {
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function addFiles(incoming: FileList | null) {
    if (!incoming) return
    const arr = Array.from(incoming)
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name))
      return [...prev, ...arr.filter((f) => !existing.has(f.name))]
    })
  }

  function removeFile(name: string) {
    setFiles((prev) => prev.filter((f) => f.name !== name))
  }

  async function handleSubmit() {
    if (files.length === 0 || sending) return
    setSending(true)
    setError(null)
    try {
      onSubmit(files)
      onClose()
    } catch {
      setError("Une erreur est survenue lors de l'envoi.")
      setSending(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/20"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-canvas rounded-2xl border border-hairline shadow-lg w-full max-w-md mx-4 p-6 flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <p className="text-[15px] font-medium text-ink">Ajouter des documents</p>
          <button
            onClick={onClose}
            className="text-[18px] text-muted hover:text-ink transition-colors leading-none"
          >
            ×
          </button>
        </div>

        {/* Zone drop */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            addFiles(e.dataTransfer.files)
          }}
          onClick={() => inputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl px-6 py-8 text-center cursor-pointer transition-colors
            ${dragging ? "border-muted bg-surface-soft" : "border-hairline hover:border-muted-soft"}
          `}
        >
          <p className="text-[13px] text-muted">
            Glisse tes fichiers ici ou <span className="underline">clique pour choisir</span>
          </p>
          <p className="text-[11px] text-muted-soft mt-1">PDF, PNG, JPG, TIFF, TXT</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.txt"
            className="hidden"
            onChange={(e) => { addFiles(e.target.files); e.target.value = "" }}
          />
        </div>

        {/* Liste des fichiers */}
        {files.length > 0 && (
          <div className="space-y-1.5 max-h-40 overflow-y-auto">
            {files.map((f) => (
              <div key={f.name} className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg bg-surface-soft">
                <span className="text-[12px] text-ink truncate">{f.name}</span>
                <button
                  onClick={() => removeFile(f.name)}
                  className="shrink-0 text-muted hover:text-ink transition-colors text-[14px] leading-none"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {error && <p className="text-[12px] text-red-500">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={files.length === 0 || sending}
          className="w-full rounded-xl border border-hairline py-2.5 text-[13px] font-medium text-ink hover:bg-surface-soft transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {sending ? "Envoi…" : "Analyser"}
        </button>
      </div>
    </div>
  )
}

// ── WikiPanel ─────────────────────────────────────────────────────────────────

export function WikiPanel() {
  const [showModal, setShowModal] = useState(false)
  const [history, setHistory] = useState<IngestionSummary[]>([])
  const [pendingFiles, setPendingFiles] = useState<string[] | null>(null)

  async function loadHistory() {
    try {
      const res = await fetch("/api/wiki/history")
      if (res.ok) setHistory(await res.json())
    } catch {}
  }

  useEffect(() => { loadHistory() }, [])

  async function handleSubmit(files: File[]) {
    const fileNames = files.map((f) => f.name)
    setPendingFiles(fileNames)

    try {
      const formData = new FormData()
      files.forEach((f) => formData.append("files", f))
      await fetch("/api/wiki/ingest", { method: "POST", body: formData })
      await loadHistory()
    } finally {
      setPendingFiles(null)
    }
  }

  return (
    <div className="px-8 py-8 max-w-2xl space-y-8">
      {showModal && (
        <UploadModal
          onClose={() => setShowModal(false)}
          onSubmit={(files) => {
            setShowModal(false)
            handleSubmit(files)
          }}
        />
      )}

      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 rounded-lg border border-hairline px-4 py-2.5 text-[13px] text-muted hover:text-ink hover:border-muted-soft transition-colors"
      >
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
          <path d="M13.5 7.5l-5.5 5.5a4 4 0 01-5.657-5.657l5.5-5.5a2.5 2.5 0 013.536 3.536l-5.507 5.507a1 1 0 01-1.414-1.414l5.5-5.5" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round"/>
        </svg>
        Ajouter un document
      </button>

      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-soft mb-3">
          Ingestions
        </p>

        <div className="space-y-2">
          {pendingFiles && <PendingCard fileNames={pendingFiles} />}

          {history.length === 0 && !pendingFiles ? (
            <p className="text-[13px] text-muted">Aucune ingestion pour l'instant.</p>
          ) : (
            history.map((e) => (
              <Link
                key={e.id}
                href={`/wiki/history/${e.id}`}
                className="block rounded-lg border border-hairline px-4 py-3 hover:border-muted-soft transition-colors"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[13px] font-medium text-ink truncate">
                    {e.files.join(", ")}
                  </p>
                  <div className="shrink-0 flex gap-2 text-[11px] font-semibold">
                    {e.sections_added > 0 && (
                      <span className="text-green-500">+{e.sections_added}</span>
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
            ))
          )}
        </div>
      </div>
    </div>
  )
}

"use client"

type DiffLine = { type: "add" | "del" | "ctx"; text: string }

type SectionAdded = { title: string; content: string }
type SectionModified = { title: string; diff_lines: DiffLine[] }
type SectionDeleted = { title: string; content: string }

export type PageChange = {
  page_title: string
  sections_added: SectionAdded[]
  sections_modified: SectionModified[]
  sections_deleted: SectionDeleted[]
}

function DiffLine({ line }: { line: DiffLine }) {
  const colors = {
    add: { bg: "bg-green-950/40", text: "text-green-300", prefix: "+" },
    del: { bg: "bg-red-950/40", text: "text-red-300", prefix: "−" },
    ctx: { bg: "", text: "text-zinc-500", prefix: " " },
  }
  const c = colors[line.type]
  return (
    <div className={`flex gap-3 px-4 py-px font-mono text-[12px] leading-5 ${c.bg}`}>
      <span className={`select-none w-3 shrink-0 ${c.text}`}>{c.prefix}</span>
      <span className={c.text}>{line.text || " "}</span>
    </div>
  )
}

function ContentBlock({ content, type }: { content: string; type: "add" | "del" }) {
  const lines = content.split("\n")
  return (
    <>
      {lines.map((line, i) => (
        <DiffLine key={i} line={{ type, text: line }} />
      ))}
    </>
  )
}

function SectionBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
        ## {title}
      </div>
      <div>{children}</div>
    </div>
  )
}

function PageBlock({ change }: { change: PageChange }) {
  const hasChanges =
    change.sections_added.length + change.sections_modified.length + change.sections_deleted.length > 0

  if (!hasChanges) return null

  return (
    <div className="mb-6 rounded-lg border border-zinc-800 overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 border-b border-zinc-800 text-[13px] font-semibold text-zinc-200">
        {change.page_title}
      </div>

      {change.sections_added.map((s) => (
        <SectionBlock key={s.title} title={s.title}>
          <ContentBlock content={s.content} type="add" />
        </SectionBlock>
      ))}

      {change.sections_modified.map((s) => (
        <SectionBlock key={s.title} title={s.title}>
          {s.diff_lines.map((line, i) => (
            <DiffLine key={i} line={line} />
          ))}
        </SectionBlock>
      ))}

      {change.sections_deleted.map((s) => (
        <SectionBlock key={s.title} title={s.title}>
          <ContentBlock content={s.content} type="del" />
        </SectionBlock>
      ))}
    </div>
  )
}

export function DiffView({ changes }: { changes: PageChange[] }) {
  if (changes.length === 0) {
    return <p className="text-sm text-zinc-500">Aucune modification détectée dans le wiki.</p>
  }

  return (
    <div>
      {changes.map((c) => (
        <PageBlock key={c.page_title} change={c} />
      ))}
    </div>
  )
}

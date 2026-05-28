import React from "react"

export function renderMarkdown(text: string): React.ReactNode {
  const paragraphs = text.split(/\n{2,}/)

  return paragraphs.map((para, pi) => {
    const lines = para.split("\n")
    const nodes: React.ReactNode[] = []

    lines.forEach((line, li) => {
      if (li > 0) nodes.push(<br key={`${pi}-br-${li}`} />)

      if (line.startsWith("### ")) {
        nodes.push(<strong key={`${pi}-h3-${li}`} className="block mt-2">{line.slice(4)}</strong>)
        return
      }
      if (line.startsWith("## ")) {
        nodes.push(<strong key={`${pi}-h2-${li}`} className="block mt-3 text-base">{line.slice(3)}</strong>)
        return
      }
      if (line.startsWith("# ")) {
        nodes.push(<strong key={`${pi}-h1-${li}`} className="block mt-4 text-lg">{line.slice(2)}</strong>)
        return
      }
      if (line.startsWith("- ") || line.startsWith("* ")) {
        nodes.push(<span key={`${pi}-li-${li}`} className="block pl-3">• {inlineMarkdown(line.slice(2))}</span>)
        return
      }

      nodes.push(...inlineMarkdown(line, `${pi}-${li}`))
    })

    return (
      <p key={pi} className={pi > 0 ? "mt-2" : ""}>
        {nodes}
      </p>
    )
  })
}

function inlineMarkdown(text: string, prefix = ""): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${prefix}-b-${i}`}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={`${prefix}-i-${i}`}>{part.slice(1, -1)}</em>
    }
    return part ? <React.Fragment key={`${prefix}-t-${i}`}>{part}</React.Fragment> : null
  }).filter(Boolean) as React.ReactNode[]
}

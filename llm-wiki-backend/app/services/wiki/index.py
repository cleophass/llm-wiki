"""Construit l'index compact du wiki — injecté dans les system prompts des agents."""

from app.db.wiki import get_wiki_pages_for_project


async def build_index(project_id: str) -> str:
    pages = await get_wiki_pages_for_project(project_id)

    if not pages:
        return "=== WIKI VIDE — aucune page encore créée ==="

    lines = ["=== WIKI DU PROJET ===", ""]
    for page in pages:
        lines.append(f"[{page.id}] {page.title}")
        if page.sections:
            for s in page.sections:
                lines.append(f"  - {s.anchor}: {s.title}")
        else:
            lines.append("  (aucune section)")
        lines.append("")

    lines.append("=== FIN DU WIKI ===")
    return "\n".join(lines)

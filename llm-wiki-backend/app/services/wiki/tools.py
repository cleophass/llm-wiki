"""Outils wiki exposés au LLM via LangChain."""

import re

from langchain_core.tools import tool

from app.db.wiki import get_wiki_page, get_wiki_pages_for_project
from app.services.wiki.index import build_index
from app.services.wiki_ingest.edit_plan import DeletePageOp, EditOp


# ── Implémentations ──────────────────────────────────────────────────────────


async def _list_pages(project_id: str) -> str:
    """Retourne l'index complet : pages + liste des sections (sans leur contenu)."""
    return await build_index(project_id)


async def _get_page_outline(page_id: str) -> str:
    """Retourne le titre et les sections d'une page, sans leur contenu."""
    page = await get_wiki_page(page_id)
    if page is None:
        return f"Page « {page_id} » introuvable."

    lines = [
        f"[{page.id}] {page.title}  (version {page.version})",
        "Sections :",
    ]
    if page.sections:
        for s in page.sections:
            lines.append(f"  - {s.anchor}: {s.title}")
    else:
        lines.append("  (aucune section)")
    return "\n".join(lines)


async def _read_section(page_id: str, anchor: str) -> str:
    """Retourne le contenu Markdown d'une section précise (identifiée par son ancre)."""
    page = await get_wiki_page(page_id)
    if page is None:
        return f"Page « {page_id} » introuvable."

    for s in page.sections:
        if s.anchor == anchor:
            if not s.content.strip():
                return f"## {s.title}\n\n(section vide)"
            return f"## {s.title}\n\n{s.content}"

    available = ", ".join(f"{s.anchor}" for s in page.sections) or "aucune"
    return (
        f"Section « {anchor} » introuvable dans la page « {page.title} ».\n"
        f"Ancres disponibles : {available}"
    )


async def _search_wiki(query: str, project_id: str) -> str:
    """Recherche un mot-clé dans les titres et contenus de sections."""
    pages = await get_wiki_pages_for_project(project_id)
    if not pages:
        return "Aucune page wiki trouvée pour ce projet."

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[str] = []

    for page in pages:
        matched: list[str] = []
        for s in page.sections:
            if pattern.search(s.title) or pattern.search(s.content):
                preview = s.content[:150].replace("\n", " ")
                matched.append(f"  [{s.anchor}] {s.title}\n    {preview}…")
        if matched or pattern.search(page.title):
            results.append(f"[{page.id}] {page.title}")
            results.extend(matched)

    if not results:
        return f"Aucune correspondance pour « {query} »."
    return "\n".join(results)


def build_wiki_tools(project_id: str, pending_ops: list[EditOp]) -> list:
    @tool
    async def list_pages() -> str:
        """Liste toutes les pages wiki du projet avec leurs sections."""
        return await _list_pages(project_id)

    @tool
    async def get_page_outline(page_id: str) -> str:
        """Retourne les sections d'une page (ancre + titre) sans leur contenu."""
        return await _get_page_outline(page_id)

    @tool
    async def read_section(page_id: str, anchor: str) -> str:
        """Retourne le contenu Markdown d'une section précise."""
        return await _read_section(page_id, anchor)

    @tool
    async def search_wiki(query: str) -> str:
        """Recherche un mot-clé dans les titres et contenus de sections du wiki."""
        return await _search_wiki(query, project_id)

    @tool
    async def delete_page(page_title: str, reason: str) -> str:
        """Planifie la suppression d'une page wiki."""
        pending_ops.append(DeletePageOp(op="delete_page", page_title=page_title, reason=reason))
        return f"Suppression planifiée pour la page « {page_title} »."

    return [list_pages, get_page_outline, read_section, search_wiki, delete_page]

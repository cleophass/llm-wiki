"""Outils wiki exposés au LLM via tool calling.

project_id est injecté par le dispatcher — jamais passé par le LLM.
"""

import logging
import re

from app.db.wiki import get_wiki_page, get_wiki_pages_for_project
from app.services.wiki.index import build_index
from app.services.wiki_ingest.edit_plan import DeletePageOp

logger = logging.getLogger(__name__)
_PENDING_OPS: list[DeletePageOp] = []


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


async def _delete_page(page_title: str, reason: str) -> str:
    """Ajoute une opération de suppression de page au plan en construction."""
    _PENDING_OPS.append(DeletePageOp(op="delete_page", page_title=page_title, reason=reason))
    return f"Suppression planifiée pour la page « {page_title} »."


def consume_pending_ops() -> list[DeletePageOp]:
    ops = list(_PENDING_OPS)
    _PENDING_OPS.clear()
    return ops


# ── Définitions JSON Schema ──────────────────────────────────────────────────

WIKI_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_pages",
            "description": (
                "Liste toutes les pages wiki du projet avec leurs sections (ancre + titre). "
                "À appeler en premier pour avoir une vue d'ensemble du wiki."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_outline",
            "description": (
                "Retourne les sections d'une page (ancre + titre) sans leur contenu. "
                "Utile pour identifier quelles sections lire avant d'appeler read_section."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ID de la page (ex: resultats_experimentation_a1b2c3).",
                    },
                },
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_section",
            "description": (
                "Retourne le contenu Markdown d'une section précise, identifiée par son ancre. "
                "Plus efficace que lire la page entière quand seule une partie est nécessaire."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ID de la page.",
                    },
                    "anchor": {
                        "type": "string",
                        "description": "Ancre de la section (ex: resultats_experimentaux).",
                    },
                },
                "required": ["page_id", "anchor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_wiki",
            "description": "Recherche un mot-clé dans les titres et contenus de sections du wiki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Mot-clé ou expression à rechercher.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_page",
            "description": (
                "Planifie la suppression d'une page wiki. À utiliser seulement après "
                "migration du contenu vers une autre page."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_title": {
                        "type": "string",
                        "description": "Titre de la page à supprimer.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Justification de la suppression (audit).",
                    },
                },
                "required": ["page_title", "reason"],
            },
        },
    },
]


# ── Dispatcher ───────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict, project_id: str) -> str:
    match name:
        case "list_pages":
            return await _list_pages(project_id)
        case "get_page_outline":
            return await _get_page_outline(args["page_id"])
        case "read_section":
            return await _read_section(args["page_id"], args["anchor"])
        case "search_wiki":
            return await _search_wiki(args["query"], project_id)
        case "delete_page":
            return await _delete_page(args["page_title"], args["reason"])
        case _:
            logger.warning("Outil inconnu : %s", name)
            return f"Outil « {name} » inconnu."

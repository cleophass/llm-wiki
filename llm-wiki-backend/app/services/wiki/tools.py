"""Outils wiki — schémas + dispatcher."""

import re

from app.db.wiki import get_wiki_page, get_wiki_pages_for_project
from app.services.wiki.index import build_index


WIKI_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_pages",
            "description": "Liste toutes les pages wiki du projet avec leurs sections.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_outline",
            "description": "Retourne les sections d'une page (ancre + titre) sans leur contenu.",
            "parameters": {
                "type": "object",
                "properties": {"page_id": {"type": "string"}},
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_section",
            "description": "Retourne le contenu Markdown d'une section précise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                    "anchor": {"type": "string"},
                },
                "required": ["page_id", "anchor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_wiki",
            "description": "Recherche un mot-clé (regex) dans les titres et contenus de sections.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


async def execute_wiki_tool(name: str, inputs: dict, project_id: str) -> str:
    if name == "list_pages":
        return await build_index(project_id)

    if name == "get_page_outline":
        page = await get_wiki_page(inputs["page_id"])
        if page is None:
            return f"Page « {inputs['page_id']} » introuvable."
        lines = [f"[{page.id}] {page.title}  (version {page.version})", "Sections :"]
        lines += [f"  - {s.anchor}: {s.title}" for s in page.sections] or ["  (aucune section)"]
        return "\n".join(lines)

    if name == "read_section":
        page = await get_wiki_page(inputs["page_id"])
        if page is None:
            return f"Page « {inputs['page_id']} » introuvable."
        for s in page.sections:
            if s.anchor == inputs["anchor"]:
                return f"## {s.title}\n\n{s.content or '(section vide)'}"
        available = ", ".join(s.anchor for s in page.sections) or "aucune"
        return f"Section « {inputs['anchor']} » introuvable. Ancres disponibles : {available}"

    if name == "search_wiki":
        pages = await get_wiki_pages_for_project(project_id)
        if not pages:
            return "Aucune page wiki trouvée."
        try:
            pattern = re.compile(inputs["query"], re.IGNORECASE)
        except re.error:
            pattern = re.compile(re.escape(inputs["query"]), re.IGNORECASE)
        results: list[str] = []
        for page in pages:
            matched = []
            for s in page.sections:
                if pattern.search(s.title) or pattern.search(s.content):
                    preview = s.content[:150].replace("\n", " ")
                    matched.append(f"  [{s.anchor}] {s.title}\n    {preview}…")
            if matched or pattern.search(page.title):
                results.append(f"[{page.id}] {page.title}")
                results.extend(matched)
        return "\n".join(results) if results else f"Aucune correspondance pour « {inputs['query']} »."

    return f"Outil inconnu : {name}"

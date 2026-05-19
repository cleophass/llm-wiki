"""CRUD wiki — stockage fichiers Markdown locaux (un fichier .md par page)."""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.wiki.models import WikiPage, WikiSection, title_to_anchor, title_to_id


def _wiki_dir() -> Path:
    path = Path(settings.wiki_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title.strip())
    return normalized.title()


def _safe_filename(title: str) -> str:
    """Transforme un titre en nom de fichier valide."""
    normalized = _normalize_title(title)
    return re.sub(r'[<>:"/\\|?*\n\r]', "_", normalized).strip() + ".md"


def _parse_file(path: Path) -> WikiPage | None:
    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").split("\n")
    title = ""
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines).strip()))

    if not title:
        title = path.stem

    updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    wiki_sections = [
        WikiSection(anchor=title_to_anchor(t), title=t, content=c)
        for t, c in sections
    ]

    return WikiPage.model_validate({
        "_id": title_to_id(title),
        "project_id": settings.global_project_id,
        "title": title,
        "sections": [s.model_dump() for s in wiki_sections],
        "version": 1,
        "created_at": updated_at,
        "updated_at": updated_at,
    })


def _write_file(path: Path, title: str, sections: list[WikiSection]) -> None:
    parts = [f"# {title}", ""]
    for s in sections:
        parts.extend([f"## {s.title}", "", s.content, ""] if s.content else [f"## {s.title}", ""])
    path.write_text("\n".join(parts), encoding="utf-8")


# ── Lectures ──────────────────────────────────────────────────────────────────


async def get_wiki_page(page_id: str) -> WikiPage | None:
    for path in _wiki_dir().glob("*.md"):
        page = _parse_file(path)
        if page and page.id == page_id:
            return page
    return None


async def get_wiki_page_by_title(project_id: str, title: str) -> WikiPage | None:
    return _parse_file(_wiki_dir() / _safe_filename(title))


async def snapshot_wiki(project_id: str) -> dict[str, dict[str, str]]:
    pages = await get_wiki_pages_for_project(project_id)
    return {page.title: {s.title: s.content for s in page.sections} for page in pages}


async def get_wiki_pages_for_project(project_id: str) -> list[WikiPage]:
    pages = []
    for path in sorted(_wiki_dir().glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        page = _parse_file(path)
        if page:
            pages.append(page)
    return pages


# ── Écritures ─────────────────────────────────────────────────────────────────


async def upsert_section(project_id: str, page_title: str, section_title: str, content: str) -> None:
    path = _wiki_dir() / _safe_filename(page_title)
    anchor = title_to_anchor(section_title)
    existing = _parse_file(path)

    if existing:
        sections = [s.model_dump() for s in existing.sections]
        found = False
        for s in sections:
            if s["anchor"] == anchor:
                s["title"] = section_title
                s["content"] = content
                found = True
                break
        if not found:
            sections.append({"anchor": anchor, "title": section_title, "content": content})
        final_sections = [WikiSection(**s) for s in sections]
    else:
        final_sections = [WikiSection(anchor=anchor, title=section_title, content=content)]

    _write_file(path, page_title, final_sections)


async def delete_section(project_id: str, page_title: str, section_title: str) -> None:
    path = _wiki_dir() / _safe_filename(page_title)
    existing = _parse_file(path)
    if not existing:
        return
    anchor = title_to_anchor(section_title)
    sections = [s for s in existing.sections if s.anchor != anchor]
    _write_file(path, page_title, sections)


async def delete_wiki_page(page_id: str) -> None:
    for path in _wiki_dir().glob("*.md"):
        page = _parse_file(path)
        if page and page.id == page_id:
            path.unlink()
            return


async def delete_wiki_page_by_title(project_id: str, title: str) -> bool:
    path = _wiki_dir() / _safe_filename(title)
    if not path.exists():
        return False
    path.unlink()
    return True

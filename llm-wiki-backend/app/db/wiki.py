"""CRUD wiki — stockage fichiers Markdown locaux (un fichier .md par page, organisé par type)."""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.wiki.models import WikiPage, WikiSection, title_to_anchor, title_to_id


def _wiki_root() -> Path:
    path = Path(settings.wiki_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _type_dir(page_type: str) -> Path:
    path = _wiki_root() / page_type
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title.strip())
    return normalized.title()


def _safe_filename(title: str) -> str:
    normalized = _normalize_title(title)
    return re.sub(r'[<>:"/\\|?*\n\r]', "_", normalized).strip() + ".md"


def _find_page_path(title: str) -> Path | None:
    """Cherche un fichier .md par titre dans tous les sous-dossiers."""
    filename = _safe_filename(title)
    for path in _wiki_root().rglob(filename):
        return path
    return None


_FRONTMATTER_RE = re.compile(r"^<!--\s*type:\s*(\w+)\s*-->$")


def _parse_file(path: Path) -> WikiPage | None:
    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").split("\n")
    page_type: str | None = None
    title = ""
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if not title and not page_type:
            m = _FRONTMATTER_RE.match(line)
            if m:
                page_type = m.group(1)
                continue
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
        "page_type": page_type,
        "sections": [s.model_dump() for s in wiki_sections],
        "version": 1,
        "created_at": updated_at,
        "updated_at": updated_at,
    })


def _write_file(path: Path, title: str, sections: list[WikiSection], page_type: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    if page_type:
        parts.append(f"<!-- type: {page_type} -->")
    parts.extend([f"# {title}", ""])
    for s in sections:
        parts.extend([f"## {s.title}", "", s.content, ""] if s.content else [f"## {s.title}", ""])
    path.write_text("\n".join(parts), encoding="utf-8")


# ── Lectures ──────────────────────────────────────────────────────────────────


async def get_wiki_page(page_id: str) -> WikiPage | None:
    for path in _wiki_root().rglob("*.md"):
        page = _parse_file(path)
        if page and page.id == page_id:
            return page
    return None


async def get_wiki_pages_for_project(project_id: str) -> list[WikiPage]:
    paths = sorted(_wiki_root().rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    pages = []
    for path in paths:
        page = _parse_file(path)
        if page:
            pages.append(page)
    return pages


async def snapshot_wiki(project_id: str) -> dict[str, dict[str, str]]:
    pages = await get_wiki_pages_for_project(project_id)
    return {page.title: {s.title: s.content for s in page.sections} for page in pages}


# ── Écritures ─────────────────────────────────────────────────────────────────


async def create_wiki_page(project_id: str, title: str, page_type: str) -> bool:
    """Crée une page vide dans wiki/{type}/. Retourne False si elle existe déjà."""
    existing = _find_page_path(title)
    if existing:
        return False
    path = _type_dir(page_type) / _safe_filename(title)
    _write_file(path, title, [], page_type=page_type)
    return True


async def upsert_section(project_id: str, page_title: str, section_title: str, content: str) -> None:
    path = _find_page_path(page_title) or (_wiki_root() / _safe_filename(page_title))
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
        _write_file(path, page_title, final_sections, page_type=existing.page_type)
    else:
        final_sections = [WikiSection(anchor=anchor, title=section_title, content=content)]
        _write_file(path, page_title, final_sections)


async def delete_section(project_id: str, page_title: str, section_title: str) -> None:
    path = _find_page_path(page_title)
    if not path:
        return
    existing = _parse_file(path)
    if not existing:
        return
    anchor = title_to_anchor(section_title)
    sections = [s for s in existing.sections if s.anchor != anchor]
    _write_file(path, page_title, sections, page_type=existing.page_type)


async def delete_wiki_page(page_id: str) -> None:
    for path in _wiki_root().rglob("*.md"):
        page = _parse_file(path)
        if page and page.id == page_id:
            path.unlink()
            return


async def delete_wiki_page_by_title(project_id: str, title: str) -> bool:
    path = _find_page_path(title)
    if not path:
        return False
    path.unlink()
    return True

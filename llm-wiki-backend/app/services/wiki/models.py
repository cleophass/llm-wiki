"""Modèles de données pour un wiki structuré par pages et sections."""

import re
import unicodedata
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _slugify(text: str) -> str:
    normalized = _normalize_text(text)
    return re.sub(r"[^a-z0-9]+", "_", normalized.lower().strip()).strip("_") or "page"


def title_to_id(title: str) -> str:
    return _slugify(title)


def title_to_anchor(title: str) -> str:
    """Transforme un titre de section en ancre stable (slug)."""
    return _slugify(title)


class WikiSection(BaseModel):
    anchor: str   # slug stable dérivé du titre
    title: str    # texte lisible de la section
    content: str = ""


class WikiPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    project_id: str
    title: str
    sections: list[WikiSection] = []
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        project_id: str,
        title: str,
        sections: list[WikiSection] | None = None,
    ) -> "WikiPage":
        return cls.model_validate({
            "_id": title_to_id(title),
            "project_id": project_id,
            "title": title,
            "sections": [s.model_dump() for s in (sections or [])],
        })

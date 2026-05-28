"""Schemas Pydantic pour les routes wiki."""

from datetime import datetime

from pydantic import BaseModel


class WikiPageSummary(BaseModel):
    page_id: str
    title: str
    page_type: str | None
    section_count: int
    updated_at: datetime | None


class WikiIndexResponse(BaseModel):
    pages: list[WikiPageSummary]


class WikiSectionDetail(BaseModel):
    anchor: str
    title: str
    content: str


class WikiPageDetail(BaseModel):
    page_id: str
    title: str
    page_type: str | None
    sections: list[WikiSectionDetail]
    version: int
    updated_at: datetime

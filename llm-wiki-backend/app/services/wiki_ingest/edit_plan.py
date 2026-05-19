"""Modèles d'opérations d'édition wiki au niveau section.

Produits par le scout, consommés par l'executor.
"""

from typing import Literal

from pydantic import BaseModel


class WriteSectionOp(BaseModel):
    op: Literal["write_section"]
    page_title: str     # titre de la page parente (créée si elle n'existe pas)
    section_title: str  # titre de la section (l'ancre est dérivée automatiquement)
    content: str        # contenu Markdown de la section


class DeleteSectionOp(BaseModel):
    op: Literal["delete_section"]
    page_title: str
    section_title: str  # la section dont l'ancre correspond sera supprimée


class DeletePageOp(BaseModel):
    op: Literal["delete_page"]
    page_title: str
    reason: str  # justification obligatoire (audit)


EditOp = WriteSectionOp | DeleteSectionOp | DeletePageOp


class EditPlan(BaseModel):
    ops: list[EditOp]

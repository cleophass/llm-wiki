from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class DocumentAnnotation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str = Field(..., min_length=1)
    nom_du_document: str | None = None
    informations_importantes: str | None = None


class ImageAnnotation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    image_type: str
    description: str = Field(
        ...,
        min_length=1,
        description=(
            "En français. "
            "Décris cette image en une phrase courte et factuelle. "
            "Conserve uniquement les informations essentielles : mesures, labels, type d'objet visible."
        ),
    )


@dataclass
class PreprocessedDocument:
    filename: str
    text: str
    annotation: DocumentAnnotation | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError(f"PreprocessedDocument '{self.filename}' has empty text.")

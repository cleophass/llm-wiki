"""Intégration OCR Mistral — extrait le texte et l'annotation d'un fichier."""

import asyncio
import base64
import io
import json
import logging
import re
from dataclasses import dataclass

from mistralai.client import Mistral
from mistralai.extra import response_format_from_pydantic_model
from pypdf import PdfReader, PdfWriter

from app.config import settings
from app.services.preprocessing.models import DocumentAnnotation, ImageAnnotation
from app.services.preprocessing.parser import ParsedFile

logger = logging.getLogger(__name__)

_OCR_MODEL = "mistral-ocr-latest"
_MAX_PAGES_PER_BATCH = 50

DOCUMENT_ANNOTATION_PROMPT = """
Tu vas recevoir un document relatif à un projet.

Génère trois champs :

1. `nom_du_document` : nom potentiel du document (ex: "Rapport", \
"Procès-verbal", "Contrat", "Plan d'architecture"). \
Mettre `null` si indéterminable.

2. `description` : description concise du contenu du document (type de document, objet principal).

3. `informations_importantes` : faits bruts et mesurables extraits du document \
(chiffres, dates, seuils, contraintes). \
Format ultra-concis, liste de paires clé=valeur séparées par des virgules \
(ex: "SLA=99.9%, budget=120k, deadline=2025-09-30"). \
N'inclure que des valeurs chiffrées ou des codes officiels. \
Mettre `null` si le document ne contient aucune information concrète et mesurable.
""".strip()


@dataclass
class OCRResult:
    text: str
    annotation: DocumentAnnotation | None


async def run_ocr(parsed_file: ParsedFile) -> OCRResult:
    """Lance l'OCR Mistral dans un thread (le SDK Mistral est synchrone)."""
    logger.info("OCR sur '%s' (%s).", parsed_file.filename, parsed_file.content_type)
    return await asyncio.to_thread(_call_api, parsed_file)


def _call_api(parsed_file: ParsedFile) -> OCRResult:
    """Worker synchrone — appelé dans un thread pool par run_ocr."""
    client = Mistral(api_key=settings.mistral_api_key)

    if parsed_file.content_type == "application/pdf":
        batches = _split_pdf_bytes(parsed_file.raw_bytes, _MAX_PAGES_PER_BATCH)
    else:
        batches = [parsed_file.raw_bytes]

    if len(batches) > 1:
        logger.info("[OCR] '%s' découpé en %d batches.", parsed_file.filename, len(batches))

    texts: list[str] = []
    annotations: list[DocumentAnnotation] = []

    for i, batch_bytes in enumerate(batches):
        batch_file = ParsedFile(
            filename=parsed_file.filename,
            content_type=parsed_file.content_type,
            raw_bytes=batch_bytes,
            requires_ocr=True,
        )
        document = _build_document_payload(batch_file)

        try:
            response = client.ocr.process(
                model=_OCR_MODEL,
                document=document,
                document_annotation_prompt=DOCUMENT_ANNOTATION_PROMPT,
                document_annotation_format=response_format_from_pydantic_model(DocumentAnnotation),
                bbox_annotation_format=response_format_from_pydantic_model(ImageAnnotation),
            )
        except Exception as exc:
            raise RuntimeError(
                f"Mistral OCR API failed for '{parsed_file.filename}' "
                f"(batch {i + 1}/{len(batches)}): {exc}"
            ) from exc

        texts.append(_extract_text(parsed_file, response))

        annotation = _safe_extract_annotation(parsed_file, response)
        if annotation is not None:
            annotations.append(annotation)

    text = "\n\n".join(texts).strip()
    if not text:
        raise RuntimeError(f"OCR returned empty text for '{parsed_file.filename}'.")

    merged_annotation = _merge_annotations(annotations) if annotations else None
    return OCRResult(text=text, annotation=merged_annotation)


def _build_document_payload(parsed_file: ParsedFile) -> dict:
    encoded = base64.standard_b64encode(parsed_file.raw_bytes).decode("utf-8")
    if parsed_file.content_type == "application/pdf":
        return {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded}"}
    return {"type": "image_url", "image_url": f"data:{parsed_file.content_type};base64,{encoded}"}


def _split_pdf_bytes(raw_bytes: bytes, max_pages: int) -> list[bytes]:
    reader = PdfReader(io.BytesIO(raw_bytes))
    total = len(reader.pages)
    if total <= max_pages:
        return [raw_bytes]
    batches: list[bytes] = []
    for start in range(0, total, max_pages):
        writer = PdfWriter()
        for page in reader.pages[start:start + max_pages]:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        batches.append(buf.getvalue())
    return batches


def _merge_annotations(annotations: list[DocumentAnnotation]) -> DocumentAnnotation | None:
    if not annotations:
        return None
    nom = next((a.nom_du_document for a in annotations if a.nom_du_document), None)
    description = next((a.description for a in annotations if a.description), None)
    infos = " | ".join(a.informations_importantes for a in annotations if a.informations_importantes) or None
    if description is None:
        return None
    return DocumentAnnotation(nom_du_document=nom, description=description, informations_importantes=infos)


def _extract_text(parsed_file: ParsedFile, response: object) -> str:
    pages = getattr(response, "pages", [])
    if not pages:
        raise RuntimeError(f"OCR returned no pages for '{parsed_file.filename}'.")
    text_parts: list[str] = []
    for page in pages:
        if not page.markdown:
            continue
        image_lookup = _build_image_lookup(page)
        enriched = _enrich_page_markdown(page.markdown, image_lookup)
        text_parts.append(enriched)
    text = "\n\n".join(text_parts).strip()
    if not text:
        raise RuntimeError(f"OCR returned empty text for '{parsed_file.filename}'.")
    logger.debug("OCR '%s': %d pages, %d chars.", parsed_file.filename, len(pages), len(text))
    return text


def _build_image_lookup(page: object) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for img in (getattr(page, "images", None) or []):
        raw = getattr(img, "image_annotation", None)
        if not raw or not isinstance(raw, str):
            continue
        try:
            data = json.loads(raw)
            annotation = ImageAnnotation.model_validate(data)
            lookup[img.id] = annotation.description
        except Exception:
            pass
    return lookup


def _enrich_page_markdown(markdown: str, image_lookup: dict[str, str]) -> str:
    if not image_lookup:
        return markdown

    def replace(match: re.Match) -> str:
        description = image_lookup.get(match.group(2))
        return f"[Image: {description}]" if description else match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]*)\)", replace, markdown)


def _safe_extract_annotation(parsed_file: ParsedFile, response: object) -> DocumentAnnotation | None:
    try:
        return _extract_annotation(parsed_file, response)
    except Exception as exc:
        logger.warning("Annotation failed for '%s': %s", parsed_file.filename, exc)
        return None


def _extract_annotation(parsed_file: ParsedFile, response: object) -> DocumentAnnotation:
    raw = getattr(response, "document_annotation", None)
    if raw is None:
        raise ValueError(f"No document_annotation in OCR response for '{parsed_file.filename}'.")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON annotation for '{parsed_file.filename}': {exc}") from exc
    elif not isinstance(raw, dict):
        raw = vars(raw) if hasattr(raw, "__dict__") else {}
    try:
        return DocumentAnnotation.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"Annotation validation failed for '{parsed_file.filename}': {exc}") from exc

import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.services.preprocessing.models import PreprocessedDocument

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES: dict[str, bool] = {
    "application/pdf": True,
    "image/jpeg": True,
    "image/png": True,
    "image/tiff": True,
    "image/webp": True,
    "text/plain": False,
}

_MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


@dataclass
class ParsedFile:
    filename: str
    content_type: str
    raw_bytes: bytes
    requires_ocr: bool


async def parse(file: UploadFile) -> ParsedFile:
    content_type = (file.content_type or "").split(";")[0].strip().lower()

    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Type '{content_type}' non supporté pour '{file.filename}'. "
            f"Types acceptés : {sorted(ALLOWED_MIME_TYPES.keys())}"
        )

    raw_bytes = await file.read()

    if not raw_bytes:
        raise ValueError(f"Le fichier '{file.filename}' est vide.")

    if len(raw_bytes) > _MAX_FILE_SIZE_BYTES:
        size_mb = len(raw_bytes) / (1024 * 1024)
        raise ValueError(f"Le fichier '{file.filename}' fait {size_mb:.1f} MB, limite : 20 MB.")

    return ParsedFile(
        filename=file.filename or "unknown",
        content_type=content_type,
        raw_bytes=raw_bytes,
        requires_ocr=ALLOWED_MIME_TYPES[content_type],
    )


async def preprocess_document(file: UploadFile) -> PreprocessedDocument:
    # Import local pour éviter une dépendance circulaire (ocr.py importe ParsedFile)
    from app.services.preprocessing.ocr import run_ocr

    parsed = await parse(file) # Verification de la conformité : type de fichier, vérification que le fichier contient bien des bytes (qu'il n'est pas vide) verification de la taille du fichier (limite à 20MB)

    if parsed.requires_ocr:
        logger.info("OCR sur '%s'.", parsed.filename)
        ocr_result = await run_ocr(parsed)
        text = ocr_result.text
        annotation = ocr_result.annotation
    else:
        try:
            text = parsed.raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Décodage UTF-8 échoué pour '{parsed.filename}': {exc}") from exc
        annotation = None

    text = text.strip()
    if not text:
        raise ValueError(f"Aucun texte extrait de '{parsed.filename}'.")

    logger.info("'%s' → %d chars, annotation=%s.", parsed.filename, len(text), "oui" if annotation else "non")
    return PreprocessedDocument(filename=parsed.filename, text=text, annotation=annotation)

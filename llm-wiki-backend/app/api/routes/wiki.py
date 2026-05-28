"""Routes wiki — ingestion et historique."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.db.ingestion_history import (
    compute_wiki_diff,
    get_ingestion_event,
    list_ingestion_events,
    save_ingestion_event,
)
from app.db.wiki import snapshot_wiki
from app.services.preprocessing.parser import preprocess_document
from app.services.wiki_ingest.executor import run_executor
from app.services.wiki_ingest.explorer import run_explorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wiki", tags=["Wiki"])


@router.post("/ingest", status_code=200, summary="Ingère un ou plusieurs documents dans le wiki global")
async def ingest_documents(files: list[UploadFile] = File(...)) -> dict:
    before = await snapshot_wiki(settings.global_project_id)
    filenames = []
    total_ops = 0

    for file in files:
        filenames.append(file.filename or "inconnu")
        doc = await preprocess_document(file)
        if not doc.text:
            logger.warning("[ingest] Fichier sans texte extrait : %s", file.filename)
            continue
        plan = await run_explorer(doc.text, settings.global_project_id)
        if plan.ops:
            await run_executor(plan, settings.global_project_id)
            total_ops += len(plan.ops)
            logger.info("[ingest] %s → %d ops.", file.filename, len(plan.ops))

    after = await snapshot_wiki(settings.global_project_id)
    changes = compute_wiki_diff(before, after)
    save_ingestion_event(filenames, changes)

    return {"ok": True, "ops": total_ops}


@router.get("/history", summary="Liste des ingestions")
async def get_history() -> list[dict]:
    return list_ingestion_events()


@router.get("/history/{event_id}", summary="Détail d'une ingestion")
async def get_history_event(event_id: str) -> dict:
    event = get_ingestion_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Ingestion introuvable.")
    return event

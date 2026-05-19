"""Executor déterministe — applique un EditPlan sur MongoDB. Pas de LLM."""

import logging

from app.db.wiki import delete_section, delete_wiki_page_by_title, upsert_section
from app.services.wiki_ingest.edit_plan import DeletePageOp, DeleteSectionOp, EditPlan, WriteSectionOp

logger = logging.getLogger(__name__)


async def _apply_delete_page(op: DeletePageOp, project_id: str) -> None:
    deleted = await delete_wiki_page_by_title(project_id, op.page_title)
    if not deleted:
        logger.info(
            "[executor] delete_page skip '%s' (introuvable)",
            op.page_title,
        )
        return
    logger.info(
        "[executor] delete_page '%s' reason='%s'",
        op.page_title,
        op.reason,
    )


async def run_executor(plan: EditPlan, project_id: str) -> None:
    """Applique toutes les opérations du plan sur MongoDB, dans l'ordre."""
    for op in plan.ops:
        try:
            match op:
                case WriteSectionOp():
                    await upsert_section(
                        project_id,
                        op.page_title,
                        op.section_title,
                        op.content,
                    )
                    logger.debug(
                        "[executor] write_section '%s' / '%s'",
                        op.page_title,
                        op.section_title,
                    )
                case DeleteSectionOp():
                    await delete_section(
                        project_id,
                        op.page_title,
                        op.section_title,
                    )
                    logger.debug(
                        "[executor] delete_section '%s' / '%s'",
                        op.page_title,
                        op.section_title,
                    )
                case DeletePageOp():
                    await _apply_delete_page(op, project_id)
        except Exception as exc:
            logger.error(
                "[executor] Échec op=%s page='%s' section='%s' : %s",
                op.op,
                op.page_title,
                getattr(op, "section_title", "?"),
                exc,
            )
            raise

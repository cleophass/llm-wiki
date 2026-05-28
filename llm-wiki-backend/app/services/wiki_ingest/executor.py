"""Executor — applique un EditPlan sur le wiki local. Pas de LLM."""

import logging

from app.config import settings
from app.db.wiki import delete_section, delete_wiki_page_by_title, upsert_section
from app.services.wiki_ingest.edit_plan import DeletePageOp, DeleteSectionOp, EditPlan, WriteSectionOp

logger = logging.getLogger(__name__)


async def run_executor(plan: EditPlan, project_id: str) -> None:
    for op in plan.ops:
        try:
            match op:
                case WriteSectionOp():
                    await upsert_section(project_id, op.page_title, op.section_title, op.content)
                    logger.debug("[executor] write_section '%s' / '%s'", op.page_title, op.section_title)
                case DeleteSectionOp():
                    await delete_section(project_id, op.page_title, op.section_title)
                    logger.debug("[executor] delete_section '%s' / '%s'", op.page_title, op.section_title)
                case DeletePageOp():
                    deleted = await delete_wiki_page_by_title(project_id, op.page_title)
                    logger.info("[executor] delete_page '%s' (trouvée=%s)", op.page_title, deleted)
        except Exception as exc:
            logger.error("[executor] Échec op=%s page='%s' : %s", op.op, op.page_title, exc)
            raise

"""Scout agent — exploration agentique du wiki et production du plan d'édition."""

import logging

from app.services.wiki.index import build_index
from app.services.wiki_ingest.agent_loop import run_wiki_agent_loop
from app.services.wiki_ingest.edit_plan import EditPlan
from app.services.wiki_ingest.prompts import SCOUT_SYSTEM
from app.services.wiki.tools import consume_pending_ops

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 15

_FINALIZE_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "finalize_writing",
        "description": "Termine l'exploration et soumet les opérations sur les sections wiki.",
        "parameters": {
            "type": "object",
            "properties": {
                "ops": {
                    "type": "array",
                    "description": "Liste des opérations à appliquer, dans l'ordre.",
                    "items": {
                        "type": "object",
                        "oneOf": [
                            {
                                "description": "Créer ou remplacer une section.",
                                "properties": {
                                    "op": {"type": "string", "enum": ["write_section"]},
                                    "page_title": {
                                        "type": "string",
                                        "description": "Titre de la page parente (créée si inexistante).",
                                    },
                                    "section_title": {
                                        "type": "string",
                                        "description": "Titre de la section (ex: 'Décisions prises').",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "Contenu Markdown factuel de la section.",
                                    },
                                },
                                "required": ["op", "page_title", "section_title", "content"],
                            },
                            {
                                "description": "Supprimer une section devenue obsolète.",
                                "properties": {
                                    "op": {"type": "string", "enum": ["delete_section"]},
                                    "page_title": {
                                        "type": "string",
                                        "description": "Titre de la page parente.",
                                    },
                                    "section_title": {
                                        "type": "string",
                                        "description": "Titre de la section à supprimer.",
                                    },
                                },
                                "required": ["op", "page_title", "section_title"],
                            },
                            {
                                "description": "Supprimer une page devenue obsolète.",
                                "properties": {
                                    "op": {"type": "string", "enum": ["delete_page"]},
                                    "page_title": {
                                        "type": "string",
                                        "description": "Titre de la page à supprimer.",
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Justification de la suppression.",
                                    },
                                },
                                "required": ["op", "page_title", "reason"],
                            },
                        ],
                    },
                },
            },
            "required": ["ops"],
        },
    },
}

_FINALIZE_TOOL_NAME = "finalize_writing"


def _build_messages(doc_text: str, wiki_index: str) -> list[dict]:
    return [
        {"role": "system", "content": SCOUT_SYSTEM.format(wiki_index=wiki_index)},
        {"role": "user", "content": doc_text},
    ]


async def run_scout(doc_text: str, project_id: str) -> EditPlan:
    wiki_index = await build_index(project_id)
    result = await run_wiki_agent_loop(
        project_id=project_id,
        messages=_build_messages(doc_text, wiki_index),
        finalize_tool=_FINALIZE_TOOL,
        finalize_tool_name=_FINALIZE_TOOL_NAME,
        max_tool_calls=MAX_TOOL_CALLS,
        label="scout",
    )
    pending_ops = consume_pending_ops()
    if not result:
        return EditPlan(ops=pending_ops)
    result = _sanitize_ops(result)
    plan = EditPlan.model_validate(result)
    if pending_ops:
        return EditPlan(ops=[*plan.ops, *pending_ops])
    return plan


def _sanitize_ops(result: dict) -> dict:
    clean = []
    for op in result.get("ops", []):
        if "op" not in op and "opop" in op:
            op = {**op, "op": op["opop"]}
        clean.append(op)
    return {**result, "ops": clean}

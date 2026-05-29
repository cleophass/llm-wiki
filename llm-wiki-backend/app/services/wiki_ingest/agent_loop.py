"""Boucle agentique — tool calling Anthropic."""

import logging
from typing import Any

from app.services.llm.client import llm_client, make_tool_result
from app.services.llm.models import LLMModel
from app.services.wiki.tools import WIKI_TOOL_SCHEMAS, execute_wiki_tool

logger = logging.getLogger(__name__)

_FINALIZE_SCHEMAS: dict[str, dict] = {
    "answer_directly": {
        "type": "function",
        "function": {
            "name": "answer_directly",
            "description": (
                "Répond directement à la question sans explorer le wiki. "
                "À utiliser uniquement si la question ne nécessite pas d'accès au wiki "
                "(salutation, question générale, reformulation, clarification)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "La réponse complète en Markdown."},
                },
                "required": ["answer"],
            },
        },
    },
    "finalize_writing": {
        "type": "function",
        "function": {
            "name": "finalize_writing",
            "description": "Soumet les opérations d'édition wiki et termine l'exploration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ops": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "oneOf": [
                                {
                                    "properties": {
                                        "op": {"type": "string", "enum": ["write_section"]},
                                        "page_title": {"type": "string"},
                                        "section_title": {"type": "string"},
                                        "content": {"type": "string"},
                                    },
                                    "required": ["op", "page_title", "section_title", "content"],
                                },
                                {
                                    "properties": {
                                        "op": {"type": "string", "enum": ["delete_section"]},
                                        "page_title": {"type": "string"},
                                        "section_title": {"type": "string"},
                                    },
                                    "required": ["op", "page_title", "section_title"],
                                },
                            ],
                        },
                    },
                },
                "required": ["ops"],
            },
        },
    },
}


async def run_wiki_agent_loop(
    *,
    project_id: str,
    messages: list[dict],
    finalize_tool_name: str = "finalize_writing",
    max_tool_calls: int = 15,
    label: str = "agent",
    output_model: Any = None,
    collect_steps: bool = False,
    model: LLMModel = LLMModel.LARGE,
) -> Any:
    history = list(messages)
    tools = WIKI_TOOL_SCHEMAS + [_FINALIZE_SCHEMAS[finalize_tool_name]]
    steps: list[dict] = []

    for step in range(max_tool_calls):
        response = await llm_client.chat_once(
            model=model,
            messages=history,
            tools=tools,
            tool_choice="required",
        )
        history.append(response.as_dict())

        if not response.tool_calls:
            logger.warning("[%s] step=%d — aucun tool call, arrêt.", label, step)
            break

        if collect_steps and response.content:
            steps.append({"type": "thought", "text": response.content})

        finalize_result = None
        for tc in response.tool_calls:
            if tc.name == finalize_tool_name:
                finalize_result = tc.arguments
                history.append(make_tool_result(tc.id, "OK"))
            else:
                tool_result = await execute_wiki_tool(tc.name, tc.arguments, project_id)
                if collect_steps:
                    steps.append({"type": "tool_call", "name": tc.name, "args": tc.arguments, "result": tool_result})
                history.append(make_tool_result(tc.id, tool_result))

        if finalize_result is not None:
            logger.info("[%s] '%s' appelé à step=%d.", label, finalize_tool_name, step)
            if output_model is not None:
                result = output_model.model_validate(finalize_result)
            else:
                result = finalize_result
            if collect_steps:
                return {"result": result, "steps": steps}
            return result

    logger.warning("[%s] terminé sans finalize.", label)
    if output_model is not None:
        result = output_model.model_validate({"ops": []})
    else:
        result = {}
    if collect_steps:
        return {"result": result, "steps": steps}
    return result

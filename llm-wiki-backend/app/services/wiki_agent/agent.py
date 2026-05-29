"""Wiki Query Agent — exploration + génération de la réponse."""

import logging

from app.db.conversations import (
    append_messages,
    set_conversation_title,
)
from app.services.llm.client import llm_client
from app.services.llm.models import LLMModel
from app.services.wiki_agent.prompts import (
    NO_ANSWER_FALLBACK,
    QUERY_SYSTEM,
    TITLE_SYSTEM,
)
from app.services.wiki_ingest.agent_loop import run_wiki_agent_loop

logger = logging.getLogger(__name__)

_AGENT_HISTORY_WINDOW = 4

_FINALIZE_TOOL_NAME = "answer_directly"



async def _call_title(question: str) -> str:
    try:
        title = await llm_client.complete(
            model=LLMModel.SMALL,
            system_prompt=TITLE_SYSTEM,
            user_prompt=question,
        )
        title = (title or "").strip()
        if title:
            return title
    except Exception:
        pass
    return " ".join(question.split()[:3])


def _build_agent_messages(question: str, wiki_index: str, history: list[dict]) -> list[dict]:
    return [
        {"role": "system", "content": QUERY_SYSTEM.format(wiki_index=wiki_index)},
        *history[-_AGENT_HISTORY_WINDOW:],
        {"role": "user", "content": question},
    ]


async def run(question: str, context: dict) -> dict:
    """Retourne {"content": str, "title": str | None}."""

    data = await run_wiki_agent_loop(
        project_id=context["project_id"],
        messages=_build_agent_messages(question, context["wiki_index"], context["history"]),
        finalize_tool_name=_FINALIZE_TOOL_NAME,
        label="wiki_query",
        collect_steps=True,
        model=LLMModel.SMALL,
    )
    answer = data["result"].get("answer", "").strip() or NO_ANSWER_FALLBACK
    steps = data["steps"]

    await append_messages(context["conversation_id"], question, answer, steps)

    title = None
    if context["is_new"]:
        title = await _call_title(question)
        await set_conversation_title(context["conversation_id"], title)

    return {"content": answer, "title": title, "steps": steps}

"""Boucle agentique LangChain pour les agents wiki."""

import logging
import os
from typing import Any

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain.agents import create_tool_calling_agent
    from langchain.agents.agent import AgentExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel

from app.config import settings
from app.services.wiki.tools import build_wiki_tools
from app.services.wiki_ingest.edit_plan import EditOp

logger = logging.getLogger(__name__)


def _configure_langsmith() -> None:
    if not settings.LANGSMITH_TRACING:
        return
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    if settings.LANGSMITH_API_KEY:
        os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)


def _build_prompt(messages: list[dict]) -> tuple[ChatPromptTemplate, str]:
    if not messages:
        return ChatPromptTemplate.from_messages([("human", "{input}")]), ""
    user_content = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
    prompt_messages: list[tuple[str, str]] = []
    for m in messages[:-1]:
        role = m["role"]
        if role == "user":
            role = "human"
        elif role == "assistant":
            role = "ai"
        prompt_messages.append((role, m["content"]))
    prompt_messages.append(("human", "{input}"))
    prompt_messages.append(("placeholder", "{agent_scratchpad}"))
    return ChatPromptTemplate.from_messages(prompt_messages), user_content


def _build_finalize_tool(finalize_tool_name: str, pending_ops: list[EditOp]):
    if finalize_tool_name == "finalize_writing":
        @tool(name=finalize_tool_name, return_direct=True)
        def finalize_writing(ops: list[dict]) -> dict:
            merged = [*ops, *[op.model_dump() for op in pending_ops]]
            return {"ops": merged}

        return finalize_writing

    if finalize_tool_name == "finalize_context":
        @tool(name=finalize_tool_name, return_direct=True)
        def finalize_context(relevant_content: str) -> dict:
            return {"relevant_content": relevant_content}

        return finalize_context

    @tool(name=finalize_tool_name, return_direct=True)
    def finalize_generic(payload: dict) -> dict:
        return payload

    return finalize_generic


async def run_wiki_agent_loop(
    *,
    project_id: str,
    messages: list[dict],
    finalize_tool: dict | None = None,
    finalize_tool_name: str = "finalize_writing",
    max_tool_calls: int = 15,
    label: str = "agent",
    output_model: type[BaseModel] | None = None,
) -> Any:
    """Exécute la boucle agentique et retourne les données de l'outil finalize."""
    _ = finalize_tool
    _configure_langsmith()
    pending_ops: list[EditOp] = []
    tools = build_wiki_tools(project_id, pending_ops)
    tools.append(_build_finalize_tool(finalize_tool_name, pending_ops))

    prompt, user_input = _build_prompt(messages)
    llm = ChatAnthropic(model=settings.anthropic_model)
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=max_tool_calls,
        verbose=False,
    )

    result: Any = await executor.ainvoke({"input": user_input})
    if output_model is not None:
        if isinstance(result, dict):
            return output_model.model_validate(result)
        logger.warning("[%s] Réponse texte sans outil finalize.", label)
        return output_model.model_validate({"ops": pending_ops})
    if not isinstance(result, dict):
        logger.warning("[%s] Réponse texte sans outil finalize.", label)
        return {}
    return result

"""Client LLM centralisé — point unique de configuration du modèle."""

import asyncio
import logging
from dataclasses import dataclass, field

import anthropic

from app.config import settings
from app.services.llm.models import LLMModel

logger = logging.getLogger(__name__)

MAX_RETRIES = 4


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ChatMessage:
    content: str | None
    tool_calls: list[ToolCall] | None = field(default=None)

    def as_dict(self) -> dict:
        content: list[dict] = []
        if self.content:
            content.append({"type": "text", "text": self.content})
        if self.tool_calls:
            for tc in self.tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
        return {"role": "assistant", "content": content}


def make_tool_result(tool_call_id: str, result: str) -> dict:
    return {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": tool_call_id, "content": result}],
    }


def _openai_tool_to_anthropic(tool: dict) -> dict:
    """Convertit un schema de tool OpenAI (wrapper 'function') au format Anthropic."""
    fn = tool["function"]
    return {
        "name": fn["name"],
        "description": fn.get("description", ""),
        "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
    }


async def _retry(attempt: int, label: str) -> None:
    wait = 2 ** attempt
    logger.warning("Rate limit — %s retry %d/%d in %ds.", label, attempt + 1, MAX_RETRIES, wait)
    await asyncio.sleep(wait)


def _extract_system(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Sépare le system prompt (top-level chez Anthropic) du reste des messages."""
    system = None
    rest = []
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        else:
            rest.append(msg)
    return system, rest


class LLMClient:
    def __init__(self, api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        *,
        model: LLMModel,
        user_prompt: str,
        system_prompt: str | None = None,
        history: list[dict] | None = None,
    ) -> str:
        """Appel simple sans tool calling — retourne du texte brut."""
        messages: list[dict] = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        kwargs: dict = {"model": model.value, "max_tokens": 4096, "messages": messages}
        if system_prompt:
            kwargs["system"] = system_prompt

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._client.messages.create(**kwargs)
                return response.content[0].text if response.content else ""
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES:
                    await _retry(attempt, "complete")
                else:
                    raise

    async def chat_once(
        self,
        *,
        model: LLMModel,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatMessage:
        """Un seul appel avec tool calling — bloquant."""
        system, rest = _extract_system(messages)
        anthropic_tools = [_openai_tool_to_anthropic(t) for t in tools]

        if tool_choice == "required":
            tc: dict = {"type": "any"}
        else:
            tc = {"type": "auto"}

        kwargs: dict = {
            "model": model.value,
            "max_tokens": 4096,
            "messages": rest,
            "tools": anthropic_tools,
            "tool_choice": tc,
        }
        if system:
            kwargs["system"] = system

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._client.messages.create(**kwargs)
                text_parts = [b.text for b in response.content if b.type == "text"]
                tool_uses = [b for b in response.content if b.type == "tool_use"]
                tool_calls = [ToolCall(id=b.id, name=b.name, arguments=b.input) for b in tool_uses] or None
                return ChatMessage(
                    content=" ".join(text_parts) or None,
                    tool_calls=tool_calls,
                )
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES:
                    await _retry(attempt, "chat_once")
                else:
                    raise


llm_client = LLMClient(api_key=settings.anthropic_api_key or "")

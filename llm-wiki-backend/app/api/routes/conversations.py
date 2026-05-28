"""Routes conversations — CRUD + endpoint de chat."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.db.conversations import (
    create_conversation,
    get_conversation,
    list_conversations,
)
from app.services.wiki.index import build_index
from app.services.wiki_agent import agent as wiki_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("")
async def get_conversations() -> list[dict]:
    return await list_conversations()


@router.post("", status_code=201)
async def new_conversation() -> dict:
    conversation_id = await create_conversation()
    return {"id": conversation_id}


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str) -> list[dict]:
    conv = await get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return conv.get("messages", [])


class MessageRequest(BaseModel):
    message: str


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, body: MessageRequest) -> JSONResponse:
    conv = await get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    history = conv.get("messages", [])
    is_new = len(history) == 0

    wiki_index = await build_index(settings.global_project_id)
    lm_history = [{"role": m["role"], "content": m["content"]} for m in history]
    
    context = {
        "conversation_id": conversation_id,
        "is_new": is_new,
        "history": lm_history,
        "wiki_index": wiki_index,
        "project_id": settings.global_project_id,
    }

    result = await wiki_agent.run(body.message, context)
    return JSONResponse({"content": result["content"], "title": result.get("title"), "steps": result.get("steps", [])})

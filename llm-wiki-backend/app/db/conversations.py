"""CRUD conversations — stockage JSON local (un fichier .json par conversation)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


def _conv_dir() -> Path:
    path = Path(settings.conversations_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _conv_path(conversation_id: str) -> Path:
    return _conv_dir() / f"{conversation_id}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(conversation_id: str) -> dict | None:
    path = _conv_path(conversation_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write(data: dict) -> None:
    _conv_path(data["id"]).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def list_conversations() -> list[dict]:
    convs = []
    for path in _conv_dir().glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        convs.append({"id": data["id"], "title": data.get("title"), "updated_at": data["updated_at"]})
    return sorted(convs, key=lambda c: c["updated_at"], reverse=True)


async def create_conversation(title: str | None = None) -> str:
    conversation_id = str(uuid.uuid4())
    now = _now()
    _write({"id": conversation_id, "title": title, "messages": [], "created_at": now, "updated_at": now})
    return conversation_id


async def get_conversation(conversation_id: str) -> dict | None:
    return _read(conversation_id)


async def append_messages(conversation_id: str, user_msg: str, assistant_msg: str, steps: list[dict] | None = None) -> None:
    data = _read(conversation_id)
    if data is None:
        return
    assistant = {"role": "assistant", "content": assistant_msg}
    if steps:
        assistant["steps"] = steps
    data["messages"].extend([
        {"role": "user", "content": user_msg},
        assistant,
    ])
    data["updated_at"] = _now()
    _write(data)


async def set_conversation_title(conversation_id: str, title: str) -> None:
    data = _read(conversation_id)
    if data is None:
        return
    data["title"] = title
    data["updated_at"] = _now()
    _write(data)

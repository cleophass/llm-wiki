"""Historique d'ingestion — stockage JSON local."""

import difflib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


def _history_dir() -> Path:
    path = Path(settings.ingestion_history_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def compute_wiki_diff(
    before: dict[str, dict[str, str]],
    after: dict[str, dict[str, str]],
) -> list[dict]:
    changes = []
    for page_title in set(before) | set(after):
        before_secs = before.get(page_title, {})
        after_secs = after.get(page_title, {})

        added, modified, deleted = [], [], []

        for sec in set(before_secs) | set(after_secs):
            if sec not in before_secs:
                added.append({"title": sec, "content": after_secs[sec]})
            elif sec not in after_secs:
                deleted.append({"title": sec, "content": before_secs[sec]})
            elif before_secs[sec] != after_secs[sec]:
                diff_lines = _build_diff_lines(before_secs[sec], after_secs[sec])
                modified.append({"title": sec, "diff_lines": diff_lines})

        if added or modified or deleted:
            changes.append({
                "page_title": page_title,
                "sections_added": added,
                "sections_modified": modified,
                "sections_deleted": deleted,
            })

    return changes


def _build_diff_lines(before: str, after: str) -> list[dict]:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    result = []
    for line in difflib.unified_diff(before_lines, after_lines, n=3):
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("+"):
            result.append({"type": "add", "text": line[1:].rstrip("\n")})
        elif line.startswith("-"):
            result.append({"type": "del", "text": line[1:].rstrip("\n")})
        else:
            result.append({"type": "ctx", "text": line[1:].rstrip("\n")})
    return result


def save_ingestion_event(files: list[str], changes: list[dict]) -> str:
    event_id = str(uuid.uuid4())
    event = {
        "id": event_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "files": files,
        "changes": changes,
    }
    (_history_dir() / f"{event_id}.json").write_text(
        json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return event_id


def list_ingestion_events() -> list[dict]:
    events = []
    for path in sorted(_history_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            event = json.loads(path.read_text(encoding="utf-8"))
            events.append({
                "id": event["id"],
                "timestamp": event["timestamp"],
                "files": event["files"],
                "pages_changed": len(event["changes"]),
                "sections_added": sum(len(c.get("sections_added", [])) for c in event["changes"]),
                "sections_modified": sum(len(c.get("sections_modified", [])) for c in event["changes"]),
                "sections_deleted": sum(len(c.get("sections_deleted", [])) for c in event["changes"]),
            })
        except Exception:
            continue
    return events


def get_ingestion_event(event_id: str) -> dict | None:
    path = _history_dir() / f"{event_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

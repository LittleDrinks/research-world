from __future__ import annotations

import json
import os
import threading
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class TraceStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)

    def create(self, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if self.path(session_id).exists():
            raise ValueError(f"session already exists: {session_id}")
        return self.append(session_id, "session_meta", data)

    def append(
        self,
        session_id: str,
        event_type: str,
        data: dict[str, Any],
        turn_id: str | None = None,
    ) -> dict[str, Any]:
        with self._locks[session_id]:
            events = self.read(session_id)
            event = _event(session_id, len(events), event_type, data, turn_id)
            _write_once(self.path(session_id), event)
        return event

    def read(self, session_id: str) -> list[dict[str, Any]]:
        path = self.path(session_id)
        if not path.exists():
            return []
        _repair_tail(path)
        return _decode_lines(path.read_bytes())

    def sessions(self) -> list[str]:
        return sorted(path.parent.name for path in self.root.glob("*/trace.jsonl"))

    def path(self, session_id: str) -> Path:
        return self.root / session_id / "trace.jsonl"


def inspect_trace(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {}
    turns = _turns(events)
    return {
        "session": events[0]["data"],
        "status": _status(turns),
        "messages": _messages(turns),
        "reports": _reports(events),
        "turns": turns,
        "events": events,
    }


def _event(session_id, seq, event_type, data, turn_id):
    event = {
        "type": event_type,
        "seq": seq,
        "time": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "data": data,
    }
    if turn_id:
        event["turn_id"] = turn_id
    return event


def _write_once(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode()
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def _repair_tail(path: Path) -> None:
    raw = path.read_bytes()
    if not raw or raw.endswith(b"\n"):
        return
    end = raw.rfind(b"\n") + 1
    with path.open("r+b") as stream:
        stream.truncate(end)


def _decode_lines(raw: bytes) -> list[dict[str, Any]]:
    events = []
    for line in raw.splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _turns(events):
    turns = {}
    for event in events:
        turn_id = event.get("turn_id")
        if turn_id:
            turns.setdefault(turn_id, {"id": turn_id, "events": []})["events"].append(
                event
            )
    return [_turn_view(value) for value in turns.values()]


def _turn_view(turn):
    events = turn["events"]
    start = next((item for item in events if item["type"] == "turn_start"), None)
    end = next((item for item in reversed(events) if item["type"] == "turn_end"), None)
    return {
        **turn,
        "input": (start or {}).get("data", {}).get("prompt", []),
        "output": (end or {}).get("data", {}).get("result_text"),
        "status": (end or {}).get("data", {}).get("status", "running"),
    }


def _messages(turns):
    messages = []
    for turn in turns:
        messages.append({"role": "user", "content": _prompt_text(turn["input"])})
        if turn["output"] is not None:
            messages.append({"role": "assistant", "content": turn["output"]})
    return messages


def _reports(events):
    values = [_report(event) for event in events if event["type"] == "tool_result"]
    return [value for value in values if value is not None]


def _report(event):
    data = event["data"]
    if data.get("name") != "publish_report" or data.get("is_error"):
        return None
    try:
        value = json.loads(data["content"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    report = _report_message(value)
    return {**report, "turn_id": event.get("turn_id"), "seq": event["seq"]} if report else None


def _report_message(value):
    if not isinstance(value, dict) or value.get("status") not in {"published", "failed"}:
        return None
    result = {"status": value["status"], "stages": _report_stages(value), "assessment": _assessment(value)}
    if value["status"] != "published":
        return result
    publication = _publication(value.get("publication"))
    return {**result, "title": value.get("title"), "publication": publication} if publication else None


def _report_stages(value):
    allowed = {"projection", "citation_validation", "rendering", "output_validation", "persistence"}
    rows = value.get("stages", [])
    return [{"name": row["name"], "status": row["status"]} for row in rows if isinstance(row, dict) and row.get("name") in allowed and row.get("status") in {"completed", "failed"}]


def _publication(value):
    if not isinstance(value, dict):
        return None
    keys = ("id", "thread_id", "created_at")
    return {key: value[key] for key in keys} if all(isinstance(value.get(key), str) for key in keys) else None


def _assessment(value):
    assessment = value.get("assessment") if isinstance(value, dict) else None
    if not isinstance(assessment, dict):
        return {"gaps": []}
    return {"delivery_level": assessment.get("delivery_level"), "minimum_source_level": assessment.get("minimum_source_level"), "gaps": _gaps(assessment.get("gaps"))}


def _gaps(value):
    return [_gap(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _gap(value):
    return {"code": value.get("code"), "path": value.get("path"), "value": _gap_value(value.get("value"))}


def _gap_value(value):
    return value if value is None or isinstance(value, (int, float, bool)) else None


def _prompt_text(blocks):
    return "\n".join(
        block.get("text", "") for block in blocks if block.get("type") == "text"
    )


def _status(turns):
    return turns[-1]["status"] if turns else "active"

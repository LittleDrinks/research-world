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
    public_events = [_public_event(event) for event in events]
    turns = _turns(public_events)
    return {
        "session": public_events[0]["data"],
        "status": _status(turns),
        "messages": _messages(turns),
        "turns": turns,
        "events": public_events,
    }


def _public_event(event):
    if event["type"] != "session_meta":
        return event
    data = {key: value for key, value in event["data"].items() if key != "runtime_binding"}
    return {**event, "data": data}


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
        "provider_items": _provider_items(events),
    }


def _messages(turns):
    messages = []
    for turn in turns:
        messages.append({"role": "user", "content": _prompt_text(turn["input"])})
        if turn["output"] is not None:
            messages.append({"role": "assistant", "content": turn["output"]})
    return messages


def _provider_items(events):
    items = {}
    for event in events:
        if event["type"] == "provider_item":
            data = event["data"]
            items[data["item"]["id"]] = {**data["item"], "phase": data["phase"]}
    return list(items.values())


def _prompt_text(blocks):
    return "\n".join(
        block.get("text", "") for block in blocks if block.get("type") == "text"
    )


def _status(turns):
    return turns[-1]["status"] if turns else "active"

from __future__ import annotations

import json
import os
import re
import threading
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CREDENTIAL_LABEL = r"(?:x[\W_]*)?api[\W_]*key|client[\W_]*secret|secret|token|password|credential|authorization"
CREDENTIAL = re.compile(rf"(?i)((?:bearer|basic)\s+|(?:{CREDENTIAL_LABEL})\s*[:=]\s*)[^\s;'\"]+")
AUTHORIZATION = re.compile(r"(?i)authorization\s*:\s*(?:bearer|basic)\s+[^\s;'\"]+")
COOKIE = re.compile(r"(?i)(?:set-)?cookie\s*:\s*[^\r\n]+")
URI = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s'\"]+")
UNIX_PATH = re.compile(r"(?<![\w:])/(?:[^\s'\"]+)")
WINDOWS_PATH = re.compile(r"(?i)\b[A-Z]:\\(?:[^\s'\"]+)")
RELATIVE_PATH = re.compile(r"(?<!\w)(?:\.{1,2}/|[\w.-]+/)[^\s'\"]+")
BARE_PATH = re.compile(r"(?<![\w.-])[\w-]+\.[A-Za-z][\w-]*(?![\w.-])")
CREDENTIAL_FIELDS = {
    "apikey", "apikeys", "xapikey", "authorization", "authorizations",
    "password", "credential", "credentials", "secret", "secrets",
    "clientsecret", "token", "tokens", "baseurl", "endpoint",
    "cookie", "cookies", "setcookie", "dsn", "databaseurl", "databaseuri",
}


class TraceStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
        self._continuations: defaultdict[str, set[str]] = defaultdict(set)

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
            event = _event(session_id, len(events), event_type, redact_trace_data(data, self._continuations[session_id]), turn_id)
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

    def remember_continuations(self, session_id: str, *values: str | None) -> None:
        self._continuations[session_id].update(value for value in values if value)


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
    data = _public_data(event["data"])
    return {**event, "data": data}


def _public_data(data):
    hidden = {"runtime_binding", "codex_home", "workspace", "provider_session_id"}
    return _redact(redact_trace_data(data), hidden, ())


def redact_trace_data(data, continuations=()):
    return _redact(_redact_continuations(data, continuations), {"workspace", "codex_home", "runtime_binding", "provider_session_id"}, ())


def _redact_continuations(value, continuations):
    if isinstance(value, dict):
        return {key: _redact_continuations(item, continuations) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_continuations(item, continuations) for item in value]
    return _redact_continuation_text(value, continuations) if isinstance(value, str) else value


def _redact_continuation_text(value, continuations):
    for continuation in continuations:
        value = value.replace(continuation, "<redacted>")
    return value


def _redact(value, hidden, path, preserved=()):
    if isinstance(value, dict):
        return {key: _redact_field(key, item, hidden, path, preserved) for key, item in value.items() if key not in hidden}
    if isinstance(value, list):
        return [_redact(item, hidden, path, preserved) for item in value]
    return _redact_text(value) if isinstance(value, str) else value


def _redact_field(key, value, hidden, path, preserved):
    if key in preserved:
        return value
    if _sensitive_field(key) and not _logical_reference(key, path):
        return "<redacted>"
    if _path_field(key):
        return "<path>"
    return _redact(value, hidden, (*path, key), preserved)


def _logical_reference(key, path):
    return key in {"endpoint", "model"} and path[-1:] == ("agent_spec",)


def _credential_field(key):
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in CREDENTIAL_FIELDS or bool(
        re.search(r"(?:^|[_-])(?:access|auth|bearer|id|refresh|session)?token$", key, re.I)
    )


def _sensitive_field(key):
    return _credential_field(key) or "cookie" in key.lower()


def _path_field(key):
    return key.lower() in {"path", "cwd"}


def _redact_text(value):
    value = URI.sub("<uri>", value)
    value = COOKIE.sub("Cookie: <redacted>", value)
    value = AUTHORIZATION.sub("Authorization: <redacted>", value)
    value = _redact_credentials(value)
    value = _redact_paths(value)
    return value


def _redact_credentials(value):
    return CREDENTIAL.sub(r"\1<redacted>", value)


def _redact_paths(value):
    value = UNIX_PATH.sub("<path>", value)
    value = WINDOWS_PATH.sub("<path>", value)
    value = RELATIVE_PATH.sub("<path>", value)
    return BARE_PATH.sub("<path>", value)


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

from __future__ import annotations

import asyncio
import os
import re
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from acp.interfaces import Client

from . import catalog
from .connectors import ConnectorStore, discover_connectors
from .endpoints import Endpoint, EndpointPool, load_endpoints
from .skills import Skill, discover_skills, skill_index
from .tools import ToolBox
from .trace import TraceStore, inspect_trace
from .types import (
    AgentSpec,
    CapabilityNotFound,
    SessionNotFound,
    SessionSpecInvalid,
)
from .types import RuntimeError as RuntimeInputError


class Runtime:
    def __init__(
        self,
        data_root: Path | None = None,
        endpoints: list[Endpoint] | None = None,
    ):
        root = Path(data_root or os.getenv("RUNTIME_DATA", "./data"))
        self.trace = TraceStore(root / "sessions")
        values = endpoints if endpoints is not None else load_endpoints()
        self.endpoints = EndpointPool(values)
        self.connectors = ConnectorStore(root / "connectors.json")
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._cancelled: set[str] = set()

    async def recognize(self, workspace: str) -> dict:
        registered = list(self.connectors.all().values())
        return await catalog.discover(
            _workspace(workspace), self.endpoints.values(), registered
        )

    def register_connector(self, value: dict[str, Any]) -> dict[str, Any]:
        return self.connectors.register(value)

    def validate_agent(self, value: dict[str, Any]) -> dict[str, bool]:
        AgentSpec.parse(value)
        return {"valid": True}

    async def launch(self, value: dict[str, Any]) -> dict[str, Any]:
        workspace = _workspace(value["workspace"])
        spec = AgentSpec.parse(value["agent_spec"])
        session_id = _session_id(value.get("session_id"))
        if self.trace.path(session_id).exists():
            _validate_existing_session(
                self.inspect(session_id)["session"],
                _launch_identity(spec, workspace, value),
            )
            return {"session_id": session_id}
        recognized = await self.recognize(str(workspace))
        _validate_spec(spec, recognized)
        meta = _session_meta(spec, workspace, value, _skill_snapshots(spec, workspace))
        self.trace.create(session_id, meta)
        return {"session_id": session_id}

    async def prompt(
        self,
        session_id: str,
        blocks: list[dict],
        client: Client | None = None,
        emit=None,
    ) -> dict:
        async with self._locks[session_id]:
            callback = emit if emit is not None else _ignore
            return await self._prompt(session_id, blocks, client, callback)

    def inspect(self, session_id: str) -> dict[str, Any]:
        events = self._events(session_id)
        return inspect_trace(events)

    async def embed(self, endpoint_id: str, model: str, texts: list[str]):
        return await self.endpoints.embed(endpoint_id, model, texts)

    def sessions(self) -> list[dict[str, Any]]:
        return [
            _session_info(self.inspect(session_id), session_id)
            for session_id in self.trace.sessions()
        ]

    def cancel(self, session_id: str) -> None:
        self._events(session_id)
        self._cancelled.add(session_id)

    async def _prompt(self, session_id, blocks, client, emit):
        events = self._events(session_id)
        meta = events[0]["data"]
        try:
            spec = AgentSpec.parse(meta["agent_spec"])
        except RuntimeInputError as error:
            raise SessionSpecInvalid(str(error)) from error
        turn_id = f"t-{uuid.uuid4().hex}"
        self.trace.append(session_id, "turn_start", {"prompt": blocks}, turn_id)
        try:
            return await self._run_turn(session_id, turn_id, spec, meta, client, emit)
        except Exception as error:
            self._fail(session_id, turn_id, error)
            raise

    async def _run_turn(self, session_id, turn_id, spec, meta, client, emit):
        skills = _skills_from_meta(meta)
        servers = self._selected_connectors(spec, Path(meta["workspace"]))
        async with ToolBox(
            Path(meta["workspace"]), skills, spec.tools, servers, client
        ) as tools:
            return await self._rounds(session_id, turn_id, spec, meta, tools, emit)

    async def _rounds(self, session_id, turn_id, spec, meta, tools, emit):
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        result = ""
        for _ in range(spec.options.max_rounds):
            if session_id in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", result, usage)
            done, result = await self._round(
                session_id, turn_id, spec, meta, tools, emit, usage
            )
            if done:
                return self._finish(session_id, turn_id, "completed", result, usage)
            if sum(usage.values()) >= spec.options.token_budget:
                break
        return self._finish(session_id, turn_id, "limit", result, usage)

    async def _round(self, session_id, turn_id, spec, meta, tools, emit, usage):
        messages = _messages(self._events(session_id), meta)
        endpoint = self.endpoints.require(spec.endpoint, spec.model)
        specs = tools.specs() if endpoint.adapter == "openai-compatible" else []
        self._record_request(session_id, turn_id, spec.model, messages, specs)
        endpoint_id, result = await self._generate(
            session_id, spec, meta, messages, specs, emit
        )
        _add_usage(usage, result.usage)
        self._record_response(session_id, turn_id, endpoint_id, result)
        calls = result.message.get("tool_calls") or []
        await self._tools(session_id, turn_id, calls, tools)
        content = result.message.get("content") or ""
        if not calls and not content.strip():
            raise RuntimeError("model returned an empty assistant response")
        return not calls, content

    def _record_request(self, session_id, turn_id, model, messages, tools):
        data = {"model": model, "messages": messages, "tools": tools}
        self.trace.append(session_id, "model_request", data, turn_id)

    async def _generate(self, session_id, spec, meta, messages, tools, emit):
        context = _provider_context(meta, self._events(session_id))
        return await self.endpoints.generate(
            spec.endpoint, spec.model, messages, tools, emit, context
        )

    def _record_response(self, session_id, turn_id, endpoint_id, result):
        data = {
            "endpoint": endpoint_id,
            "message": result.message,
            "usage": result.usage,
            "provider_session_id": result.provider_session_id,
        }
        self.trace.append(session_id, "model_response", data, turn_id)

    async def _tools(self, session_id, turn_id, calls, tools):
        for call in calls:
            function = call.get("function") or {}
            data = {
                "tool_call_id": call.get("id"),
                "name": function.get("name"),
                "arguments": function.get("arguments", ""),
            }
            self.trace.append(session_id, "tool_call", data, turn_id)
            content, failed = await tools.call(
                session_id, data["name"], data["arguments"]
            )
            result = {**data, "content": content, "is_error": failed}
            self.trace.append(session_id, "tool_result", result, turn_id)

    def _finish(self, session_id, turn_id, status, result, usage):
        self._cancelled.discard(session_id)
        self.trace.append(
            session_id,
            "turn_end",
            {"status": status, "result_text": result, "usage": usage},
            turn_id,
        )
        return {"status": status, "result_text": result, "usage": usage}

    def _fail(self, session_id, turn_id, error):
        message = {"error": f"{type(error).__name__}: {error}"}
        self.trace.append(session_id, "error", message, turn_id)
        self.trace.append(
            session_id, "turn_end", {"status": "error", "result_text": None}, turn_id
        )

    def _events(self, session_id):
        events = self.trace.read(session_id)
        if not events:
            raise SessionNotFound(session_id)
        return events

    def _selected_connectors(self, spec: AgentSpec, workspace: Path):
        registered = self.connectors.all().values()
        available = discover_connectors(workspace, registered)
        return [available[name] for name in spec.connectors]


async def _ignore(text: str) -> None:
    return None


def _workspace(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_absolute() or not path.is_dir():
        raise ValueError("workspace must be an existing directory")
    return path


def _session_id(value: str | None) -> str:
    session_id = value or f"s-{uuid.uuid4().hex}"
    if not re.fullmatch(r"s-[A-Za-z0-9_-]{1,64}", session_id):
        raise ValueError("invalid session id")
    return session_id


def _validate_existing_session(current: dict, expected: dict) -> None:
    current_spec = AgentSpec.parse(current["agent_spec"]).snapshot()
    same_spec = current_spec == expected["agent_spec"]
    keys = ("workspace", "parent", "mode")
    if not same_spec or any(current.get(key) != expected.get(key) for key in keys):
        raise ValueError("session id belongs to a different launch")


def _launch_identity(spec, workspace, value) -> dict:
    return {
        "workspace": str(workspace),
        "agent_spec": spec.snapshot(),
        "parent": value.get("parent"),
        "mode": value.get("mode", "resume"),
    }


def _validate_spec(spec: AgentSpec, recognized: dict) -> None:
    endpoint_ids = {item["id"] for item in recognized["endpoints"] if item["available"]}
    model_pairs = {(item["endpoint"], item["id"]) for item in recognized["models"]}
    _require(spec.endpoint, endpoint_ids, "endpoint")
    _require((spec.endpoint, spec.model), model_pairs, "model")
    for key in ("skills", "tools", "connectors"):
        available = {
            item["id"] for item in recognized[key] if item.get("available", True)
        }
        for value in getattr(spec, key):
            _require(value, available, _capability_kind(key))


def _require(value, available, kind):
    if value not in available:
        raise CapabilityNotFound(f"{kind} is not available: {value}")


def _capability_kind(key: str) -> str:
    return key[:-1]


def _session_meta(spec, workspace, value, skills):
    return {
        "agent_spec": spec.snapshot(),
        "workspace": str(workspace),
        "parent": value.get("parent"),
        "mode": value.get("mode", "resume"),
        "skills": skills,
    }


def _skill_snapshots(spec: AgentSpec, workspace: Path):
    available = discover_skills(workspace)
    return [
        {**available[name].public(), "body": available[name].body()}
        for name in spec.skills
    ]


class _SnapshotSkill:
    def __init__(self, value):
        self.id = value["id"]
        self.name = value["name"]
        self.description = value["description"]
        self._body = value["body"]

    def body(self):
        return self._body


def _skills_from_meta(meta) -> dict[str, Skill]:
    return {value["id"]: _SnapshotSkill(value) for value in meta.get("skills", [])}


def _messages(events, meta):
    messages = [{"role": "system", "content": _system_prompt(meta)}]
    for event in events:
        _append_message(messages, event)
    return messages


def _system_prompt(meta):
    spec = AgentSpec.parse(meta["agent_spec"])
    skills = _skills_from_meta(meta)
    parts = [spec.instructions, skill_index(list(skills.values()))]
    if "read_resource" in spec.tools:
        parts.append(
            "References written as @node_id are available through read_resource."
        )
    return "\n\n".join(part for part in parts if part)


def _append_message(messages, event):
    if event["type"] == "turn_start":
        messages.append(
            {"role": "user", "content": _prompt_content(event["data"]["prompt"])}
        )
    elif event["type"] == "model_response":
        messages.append(event["data"]["message"])
    elif event["type"] == "tool_result":
        data = event["data"]
        messages.append(
            {
                "role": "tool",
                "tool_call_id": data["tool_call_id"],
                "content": data["content"],
            }
        )


def _prompt_content(blocks):
    parts = []
    for block in blocks:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif block.get("type") == "resource_link":
            parts.append(f"@{block.get('uri', '')}")
    return "\n".join(parts)


def _provider_context(meta, events):
    options = meta["agent_spec"].get("options", {})
    return {
        "workspace": meta["workspace"],
        "sandbox": options.get("sandbox", "read-only"),
        "reasoning_effort": options.get("reasoning_effort", "medium"),
        "provider_session_id": _provider_session(events),
    }


def _provider_session(events):
    for event in reversed(events):
        if event["type"] == "model_response" and event["data"].get(
            "provider_session_id"
        ):
            return event["data"]["provider_session_id"]
    return None


def _add_usage(total, current):
    for key in total:
        total[key] += current.get(key, 0)


def _session_info(view, session_id):
    session = view["session"]
    return {
        "session_id": session_id,
        "cwd": session["workspace"],
        "title": session["agent_spec"]["name"],
        "updated_at": view["events"][-1]["time"],
    }

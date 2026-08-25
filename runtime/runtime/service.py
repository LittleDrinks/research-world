from __future__ import annotations

import asyncio
import os
import re
import uuid
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from acp.interfaces import Client

from . import catalog
from .adapters import ToolDefinition, discover_adapters
from .endpoints import Endpoint, EndpointPool, load_endpoints
from .runtimes import (
    CodexRuntimeAdapter,
    RuntimeAdapter,
    RuntimePool,
    codex_endpoint,
    load_runtimes,
)
from .skills import Skill, discover_skills, skill_index
from .tools import ToolBox
from .trace import TraceStore, inspect_trace
from .types import (
    AgentSpec,
    CapabilityNotFound,
    SessionNotFound,
    SessionSpecInvalid,
    ToolPlanDrift,
    TraceError,
)
from .types import RuntimeError as RuntimeInputError


class Runtime:
    def __init__(
        self,
        data_root: Path | None = None,
        endpoints: list[Endpoint] | None = None,
        runtimes: list[RuntimeAdapter] | None = None,
        tool_definitions: Iterable[ToolDefinition] = (),
    ):
        root = Path(data_root or os.getenv("RUNTIME_DATA", "./data"))
        self.trace = TraceStore(root / "sessions")
        values = endpoints if endpoints is not None else load_endpoints()
        adapters = runtimes if runtimes is not None else load_runtimes()
        _bind_endpoint_ids(adapters, values)
        self.runtimes = RuntimePool(adapters)
        self.endpoints = EndpointPool(_runtime_endpoints(values, adapters))
        self.tool_definitions = tuple(tool_definitions)
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._cancelled: set[tuple[str, str]] = set()
        self._active_turns: dict[str, tuple[str, RuntimeAdapter]] = {}

    async def recognize(self, workspace: str) -> dict:
        path = _workspace(workspace)
        adapters = discover_adapters(path, self.tool_definitions)
        return await catalog.discover(
            path, self.endpoints.values(), self.runtimes, adapters
        )

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
        _validate_spec(spec, recognized, self.runtimes.require(spec.runtime))
        snapshots = _skill_snapshots(spec, workspace)
        plan = await self._tool_plan(spec, workspace, snapshots)
        meta = _session_meta(spec, workspace, value, snapshots, plan, recognized)
        self.trace.create(session_id, meta)
        return {"session_id": session_id}

    async def _tool_plan(self, spec: AgentSpec, workspace: Path, snapshots) -> list:
        skills = {value["id"]: _SnapshotSkill(value) for value in snapshots}
        adapters = discover_adapters(workspace, self.tool_definitions)
        async with ToolBox(workspace, skills, spec.tools, adapters, None) as tools:
            return tools.plan()

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

    def default_endpoint(self, descriptor) -> Endpoint:
        adapter = self.runtimes.require(descriptor)
        endpoint = next(
            (item for item in self.endpoints.values() if adapter.accepts(item)), None
        )
        if endpoint is None:
            raise CapabilityNotFound("no model endpoint is available for runtime")
        return endpoint

    def cancel(self, session_id: str) -> None:
        active = self._active_turns.get(session_id)
        if active is None:
            return
        turn_id, adapter = active
        self._cancelled.add((session_id, turn_id))
        adapter.cancel(session_id)

    async def _prompt(self, session_id, blocks, client, emit):
        events = self._events(session_id)
        meta = events[0]["data"]
        try:
            spec = AgentSpec.parse(meta["agent_spec"])
        except RuntimeInputError as error:
            raise SessionSpecInvalid(str(error)) from error
        turn_id = f"t-{uuid.uuid4().hex}"
        self.trace.append(session_id, "turn_start", {"prompt": blocks}, turn_id)
        adapter = self.runtimes.require(spec.runtime)
        self._active_turns[session_id] = (turn_id, adapter)
        try:
            return await self._run_turn(session_id, turn_id, spec, meta, client, emit)
        except Exception as error:
            if (session_id, turn_id) in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", "", {})
            self._fail(session_id, turn_id, error)
            raise
        finally:
            self._active_turns.pop(session_id, None)

    async def _run_turn(self, session_id, turn_id, spec, meta, client, emit):
        skills = _skills_from_meta(meta)
        workspace = Path(meta["workspace"])
        adapters = discover_adapters(workspace, self.tool_definitions)
        async with ToolBox(workspace, skills, spec.tools, adapters, client) as tools:
            _require_frozen_plan(tools.plan(), meta.get("tool_plan"))
            return await self._rounds(session_id, turn_id, spec, meta, tools, emit)

    async def _rounds(self, session_id, turn_id, spec, meta, tools, emit):
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        result = ""
        for _ in range(spec.options.max_rounds):
            if (session_id, turn_id) in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", result, usage)
            done, result = await self._round(
                session_id, turn_id, spec, meta, tools, emit, usage
            )
            if (session_id, turn_id) in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", result, usage)
            if done:
                return self._finish(session_id, turn_id, "completed", result, usage)
            if sum(usage.values()) >= spec.options.token_budget:
                break
        return self._finish(session_id, turn_id, "limit", result, usage)

    async def _round(self, session_id, turn_id, spec, meta, tools, emit, usage):
        messages = _messages(self._events(session_id), meta)
        endpoint = self.endpoints.require(spec.endpoint, spec.model)
        specs = (
            tools.specs() if not self.runtimes.require(spec.runtime).owns_process else []
        )
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
        endpoint = self.endpoints.require(spec.endpoint, spec.model)
        adapter = self.runtimes.require(spec.runtime)
        if adapter.owns_process:
            return await adapter.generate(
                session_id, endpoint, spec.model, messages, tools, emit, context
            )
        return endpoint.id, await endpoint.provider.generate(
            spec.model, messages, tools, emit, context
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
        self._cancelled.discard((session_id, turn_id))
        self.trace.append(
            session_id,
            "turn_end",
            {"status": status, "result_text": result, "usage": usage},
            turn_id,
        )
        return {"status": status, "result_text": result, "usage": usage}

    def _fail(self, session_id, turn_id, error):
        message = {"code": _error_code(error), "message": str(error)}
        self.trace.append(session_id, "error", message, turn_id)
        self.trace.append(
            session_id, "turn_end", {"status": "error", "result_text": None}, turn_id
        )

    def _events(self, session_id):
        events = self.trace.read(session_id)
        if not events:
            raise SessionNotFound(session_id)
        return events


async def _ignore(text: str) -> None:
    return None


def _workspace(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_absolute() or not path.is_dir():
        raise ValueError("workspace must be an existing directory")
    return path


def _codex_endpoints(adapters: list[RuntimeAdapter]) -> list[Endpoint]:
    values = [
        item
        for item in adapters
        if isinstance(item, CodexRuntimeAdapter) and item.descriptor.status == "ready"
    ]
    return [codex_endpoint(_codex_model()) for _ in values]


def _runtime_endpoints(values, adapters) -> list[Endpoint]:
    existing = {item.id for item in values}
    return [
        *values,
        *(item for item in _codex_endpoints(adapters) if item.id not in existing),
    ]


def _bind_endpoint_ids(adapters, endpoints) -> None:
    ids = tuple(item.id for item in endpoints)
    for adapter in adapters:
        if adapter.descriptor.id == "openai-compatible":
            adapter.endpoint_ids = ids


def _codex_model() -> str:
    return os.getenv("CODEX_MODEL", "gpt-5.6-sol")


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


def _validate_spec(spec: AgentSpec, recognized: dict, runtime) -> None:
    _validate_runtime(spec, recognized)
    endpoint = _validate_endpoint(spec, recognized)
    if not runtime.accepts(endpoint):
        raise CapabilityNotFound("endpoint is not available for runtime")
    _validate_dependencies(spec, recognized)


def _validate_runtime(spec, recognized) -> None:
    runtimes = {
        (item["id"], item["realm"])
        for item in recognized["runtimes"]
        if item["status"] == "ready"
    }
    _require((spec.runtime.id, spec.runtime.realm), runtimes, "runtime")


def _validate_endpoint(spec, recognized) -> dict:
    endpoint_ids = {item["id"] for item in recognized["endpoints"] if item["available"]}
    model_pairs = {(item["endpoint"], item["id"]) for item in recognized["models"]}
    _require(spec.endpoint, endpoint_ids, "endpoint")
    endpoint = next(
        item for item in recognized["endpoints"] if item["id"] == spec.endpoint
    )
    _require((spec.endpoint, spec.model), model_pairs, "model")
    return endpoint


def _validate_dependencies(spec, recognized) -> None:
    skills = {item["id"] for item in recognized["skills"]}
    for value in spec.skills:
        _require(value, skills, "skill")
    ready = {item["id"] for item in recognized["tools"] if item["status"] == "ready"}
    for value in spec.tools:
        _require(value, ready, "tool")


def _require(value, available, kind):
    if value not in available:
        raise CapabilityNotFound(f"{kind} is not available: {value}")


def _session_meta(spec, workspace, value, skills, tool_plan, capabilities):
    return {
        "agent_spec": spec.snapshot(),
        "workspace": str(workspace),
        "parent": value.get("parent"),
        "mode": value.get("mode", "resume"),
        "skills": skills,
        "tool_plan": tool_plan,
        "capability_snapshot": _capability_snapshot(spec, capabilities),
    }


def _capability_snapshot(spec, recognized):
    runtime = next(
        item
        for item in recognized["runtimes"]
        if (item["id"], item["realm"]) == (spec.runtime.id, spec.runtime.realm)
    )
    return {"runtime": runtime}


def _require_frozen_plan(current: list, frozen: list | None) -> None:
    if current != frozen:
        raise ToolPlanDrift("tool operations changed since launch; start a new session")


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
        "runtime_session_id": events[0]["session_id"],
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


def _error_code(error: Exception) -> str:
    return error.code if isinstance(error, TraceError) else "runtime_error"


def _session_info(view, session_id):
    session = view["session"]
    return {
        "session_id": session_id,
        "cwd": session["workspace"],
        "title": session["agent_spec"]["name"],
        "updated_at": view["events"][-1]["time"],
    }

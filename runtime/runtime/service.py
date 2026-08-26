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
from .config import prepare_session_auth
from .adapters import ToolDefinition, discover_adapters
from .endpoints import Endpoint, EndpointPool, load_endpoints
from .runtimes import (
    CodexRuntimeAdapter,
    RuntimeAdapter,
    RuntimePool,
    load_runtimes,
)
from .session_state import SessionStateStore
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
        self.trace, self.state = _session_stores(root)
        values = endpoints if endpoints is not None else load_endpoints()
        adapters = runtimes if runtimes is not None else load_runtimes()
        _bind_endpoint_ids(adapters, values)
        self.runtimes = RuntimePool(adapters)
        self.endpoints = EndpointPool(values)
        self.tool_definitions = tuple(tool_definitions)
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._cancelled: set[tuple[str, str]] = set()
        self._active_turns: dict[str, tuple[str, RuntimeAdapter]] = {}
        self._bindings: dict[str, _LaunchBinding] = {}

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
            self._validate_launch(session_id, spec, workspace, value)
        else:
            await self._create_session(session_id, spec, workspace, value)
        return {"session_id": session_id}

    def _validate_launch(self, session_id, spec, workspace, value) -> None:
        state = self.state.read(session_id)
        _validate_existing_session(state, _launch_identity(spec, workspace, value))

    async def _create_session(self, session_id, spec, workspace, value) -> None:
        recognized = await self.recognize(str(workspace))
        adapter = self.runtimes.require(spec.runtime)
        _validate_spec(spec, recognized, adapter)
        endpoint = _launch_endpoint(self.endpoints, spec, adapter)
        snapshots = _skill_snapshots(spec, workspace)
        plan = await self._tool_plan(spec, workspace, snapshots)
        meta = _session_meta(spec, value, snapshots, plan, recognized, endpoint)
        state = _session_state(spec, workspace, value, self.trace.path(session_id), adapter)
        self.state.create(session_id, state)
        self.trace.create(session_id, meta)
        self._bindings[session_id] = _LaunchBinding(adapter, endpoint, spec)

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
        _session_spec(events)
        binding = self._binding(session_id)
        spec, meta = binding.spec, events[0]["data"]
        turn_id = f"t-{uuid.uuid4().hex}"
        self._begin_turn(session_id, turn_id, blocks, binding.adapter)
        try:
            return await self._run_turn(session_id, turn_id, binding, meta, client, emit)
        except asyncio.CancelledError:
            self._finish(session_id, turn_id, "cancelled", "", {})
            raise
        except Exception as error:
            return self._handle_turn_error(session_id, turn_id, error)
        finally:
            self._active_turns.pop(session_id, None)

    def _begin_turn(self, session_id, turn_id, blocks, adapter) -> None:
        self.trace.append(session_id, "turn_start", {"prompt": blocks}, turn_id)
        self._active_turns[session_id] = (turn_id, adapter)

    def _handle_turn_error(self, session_id, turn_id, error):
        if (session_id, turn_id) in self._cancelled:
            return self._finish(session_id, turn_id, "cancelled", "", {})
        self._fail(session_id, turn_id, error)
        raise error

    async def _run_turn(self, session_id, turn_id, binding, meta, client, emit):
        spec = binding.spec
        skills = _skills_from_meta(meta)
        workspace = Path(self.state.read(session_id)["workspace"])
        adapters = discover_adapters(workspace, self.tool_definitions)
        async with ToolBox(workspace, skills, spec.tools, adapters, client) as tools:
            _require_frozen_plan(tools.plan(), meta.get("tool_plan"))
            return await self._rounds(session_id, turn_id, binding, meta, tools, emit)

    async def _rounds(self, session_id, turn_id, binding, meta, tools, emit):
        spec = binding.spec
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        result, provider_session_id = "", None
        for _ in range(spec.options.max_rounds):
            if (session_id, turn_id) in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", result, usage)
            done, result, provider_session_id = await self._round(
                session_id, turn_id, binding, meta, tools, emit, usage
            )
            if (session_id, turn_id) in self._cancelled:
                return self._finish(session_id, turn_id, "cancelled", result, usage)
            if done:
                return self._finish(session_id, turn_id, "completed", result, usage, provider_session_id)
            if sum(usage.values()) >= spec.options.token_budget:
                break
        return self._finish(session_id, turn_id, "limit", result, usage, provider_session_id)

    async def _round(self, session_id, turn_id, binding, meta, tools, emit, usage):
        spec = binding.spec
        messages = _messages(self._events(session_id), meta)
        specs = (
            tools.specs() if not binding.adapter.owns_process else []
        )
        self._record_request(session_id, turn_id, spec.model, messages, specs)
        endpoint_id, result = await self._generate(
            session_id, binding, meta, messages, specs, emit
        )
        _add_usage(usage, result.usage)
        self._record_response(session_id, turn_id, endpoint_id, result)
        calls = result.message.get("tool_calls") or []
        await self._tools(session_id, turn_id, calls, tools)
        content = result.message.get("content") or ""
        if not calls and not content.strip():
            raise RuntimeError("model returned an empty assistant response")
        return not calls, content, result.provider_session_id

    def _record_request(self, session_id, turn_id, model, messages, tools):
        data = {"model": model, "messages": messages, "tools": tools}
        self.trace.append(session_id, "model_request", data, turn_id)

    async def _generate(self, session_id, binding, meta, messages, tools, emit):
        context = _provider_context(meta, self.state.read(session_id), self._events(session_id))
        endpoint, adapter, spec = binding.endpoint, binding.adapter, binding.spec
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
        }
        self.trace.append(session_id, "model_response", data, turn_id)
        for item in result.provider_items:
            self.trace.append(session_id, "provider_item", item, turn_id)

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

    def _finish(self, session_id, turn_id, status, result, usage, provider_session_id=None):
        if (session_id, turn_id) in self._cancelled:
            status = "cancelled"
        self._cancelled.discard((session_id, turn_id))
        self.trace.append(
            session_id,
            "turn_end",
            {"status": status, "result_text": result, "usage": usage},
            turn_id,
        )
        if status in {"completed", "limit"} and provider_session_id:
            self.state.update(session_id, {"provider_session_id": provider_session_id})
        return {"status": status, "result_text": result, "usage": usage}

    def _fail(self, session_id, turn_id, error):
        for item in getattr(error, "provider_items", []):
            self.trace.append(session_id, "provider_item", item, turn_id)
        if terminal := getattr(error, "provider_terminal", None):
            self.trace.append(session_id, "provider_terminal", terminal, turn_id)
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

    def _binding(self, session_id):
        binding = self._bindings.get(session_id)
        if binding is None:
            binding = _restore_binding(self._events(session_id), self.state.read(session_id), self.runtimes, self.endpoints)
            self._bindings[session_id] = binding
        return binding


async def _ignore(text: str) -> None:
    return None


def _session_stores(root):
    return TraceStore(root / "sessions"), SessionStateStore(root / "session-state")


def _workspace(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_absolute() or not path.is_dir():
        raise ValueError("workspace must be an existing directory")
    return path


def _session_spec(events):
    meta = events[0]["data"]
    try:
        return AgentSpec.parse(meta["agent_spec"]), meta
    except RuntimeInputError as error:
        raise SessionSpecInvalid(str(error)) from error


def _bind_endpoint_ids(adapters, endpoints) -> None:
    ids = tuple(item.id for item in endpoints)
    for adapter in adapters:
        if adapter.descriptor.id == "openai-compatible":
            adapter.endpoint_ids = ids


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
    endpoint = _validate_endpoint(spec, recognized, not runtime.owns_process)
    if not runtime.accepts(endpoint):
        raise CapabilityNotFound("endpoint is not available for runtime")
    if runtime.owns_process and spec.tools:
        raise CapabilityNotFound("codex cannot expose selected Tool schemas")
    _validate_dependencies(spec, recognized)


def _validate_runtime(spec, recognized) -> None:
    runtimes = {
        (item["id"], item["realm"])
        for item in recognized["runtimes"]
        if item["status"] == "ready"
    }
    _require((spec.runtime.id, spec.runtime.realm), runtimes, "runtime")


def _validate_endpoint(spec, recognized, require_ready) -> dict:
    endpoint_ids = {item["id"] for item in recognized["endpoints"] if item["available"] or not require_ready}
    model_pairs = _model_pairs(recognized, require_ready)
    _require(spec.endpoint, endpoint_ids, "endpoint")
    endpoint = next(
        item for item in recognized["endpoints"] if item["id"] == spec.endpoint
    )
    _require((spec.endpoint, spec.model), model_pairs, "model")
    return endpoint


def _model_pairs(recognized, require_ready):
    if require_ready:
        return {(item["endpoint"], item["id"]) for item in recognized["models"]}
    return {(item["id"], model) for item in recognized["endpoints"] for model in item["models"]}


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


def _session_meta(spec, value, skills, tool_plan, capabilities, endpoint):
    return {
        "agent_spec": spec.snapshot(),
        "parent": value.get("parent"),
        "mode": value.get("mode", "resume"),
        "skills": skills,
        "tool_plan": tool_plan,
        "capability_snapshot": _capability_snapshot(spec, capabilities),
        "endpoint_snapshot": endpoint.public(),
    }


def _session_state(spec, workspace, value, trace_path, adapter):
    state = {**_launch_identity(spec, workspace, value), "runtime_binding": _adapter_identity(adapter)}
    if spec.runtime.id == "codex":
        home = trace_path.parent / "codex-home"
        prepare_session_auth(home)
        state["codex_home"] = str(home)
    return state


def _capability_snapshot(spec, recognized):
    runtime = next(
        item
        for item in recognized["runtimes"]
        if (item["id"], item["realm"]) == (spec.runtime.id, spec.runtime.realm)
    )
    return {"runtime": runtime}


class _LaunchBinding:
    def __init__(self, adapter, endpoint, spec):
        self.adapter = adapter
        self.endpoint = endpoint
        self.spec = spec


def _restore_binding(events, state, runtimes, endpoints):
    _, meta = _session_spec(events)
    spec = AgentSpec.parse(meta["agent_spec"])
    adapter = runtimes.require(spec.runtime)
    endpoint = _persisted_endpoint(endpoints, spec, adapter)
    _require_binding_snapshot(meta, state, adapter, endpoint)
    return _LaunchBinding(adapter, endpoint, spec)


def _launch_endpoint(endpoints, spec, adapter):
    return endpoints.resolve(spec.endpoint, spec.model) if adapter.owns_process else endpoints.require(spec.endpoint, spec.model)


def _persisted_endpoint(endpoints, spec, adapter):
    try:
        return _launch_endpoint(endpoints, spec, adapter)
    except CapabilityNotFound as error:
        raise SessionSpecInvalid("persisted endpoint binding is unavailable") from error


def _require_binding_snapshot(meta, state, adapter, endpoint) -> None:
    snapshot = meta.get("capability_snapshot", {}).get("runtime")
    if not isinstance(snapshot, dict) or not isinstance(meta.get("endpoint_snapshot"), dict):
        raise SessionSpecInvalid("session launch binding is unavailable")
    if not _same_runtime(snapshot, adapter.descriptor.public()):
        raise SessionSpecInvalid("persisted runtime binding is unavailable")
    if meta["endpoint_snapshot"] != endpoint.public():
        raise SessionSpecInvalid("persisted endpoint binding is unavailable")
    _require_executable_identity(state, adapter)


def _require_executable_identity(state, adapter) -> None:
    expected = state.get("runtime_binding")
    actual = _adapter_identity(adapter)
    if expected != actual:
        raise SessionSpecInvalid("persisted runtime executable is unavailable")


def _adapter_identity(adapter):
    if isinstance(adapter, CodexRuntimeAdapter):
        return adapter.provider.executable_identity
    return None


def _same_runtime(expected, actual) -> bool:
    ignored = {"last_checked_at"}
    left = {key: value for key, value in expected.items() if key not in ignored}
    right = {key: value for key, value in actual.items() if key not in ignored}
    return left == right


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
    replayable = _replayable_turns(events)
    for event in events:
        if event.get("turn_id") in replayable:
            _append_message(messages, event)
    return messages


def _replayable_turns(events) -> set[str]:
    completed = {
        event["turn_id"]
        for event in events
        if event["type"] == "turn_end"
        and event["data"]["status"] in {"completed", "limit"}
    }
    return completed | _latest_open_turn(events)


def _latest_open_turn(events) -> set[str]:
    ended = {event["turn_id"] for event in events if event["type"] == "turn_end"}
    starts = [event["turn_id"] for event in events if event["type"] == "turn_start"]
    return {starts[-1]} if starts and starts[-1] not in ended else set()


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


def _provider_context(meta, state, events):
    options = meta["agent_spec"].get("options", {})
    return {
        "workspace": state["workspace"],
        "sandbox": options.get("sandbox", "read-only"),
        "reasoning_effort": options.get("reasoning_effort", "medium"),
        "runtime_session_id": events[0]["session_id"],
        "provider_session_id": state.get("provider_session_id"),
        "codex_home": state.get("codex_home", ""),
    }


def _add_usage(total, current):
    for key, value in current.items():
        total[key] = total.get(key, 0) + value


def _error_code(error: Exception) -> str:
    return error.code if isinstance(error, TraceError) else "runtime_error"


def _session_info(view, session_id):
    session = view["session"]
    return {
        "session_id": session_id,
        "cwd": None,
        "title": session["agent_spec"]["name"],
        "updated_at": view["events"][-1]["time"],
    }

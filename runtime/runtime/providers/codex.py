from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import CollectedResult, Emit, ModelResult
from ..config import prepare_session_auth
from ..types import TraceError

try:
    import fcntl
except ImportError:
    fcntl = None

VERSION = re.compile(r"codex-cli\s+(\S+)")
COMPATIBLE_VERSION = "0.149.1"
TERMINALS = {"turn.completed", "turn.failed"}
ITEM_EVENTS = {"item.started", "item.updated", "item.completed"}
EVENTS = {"thread.started", "turn.started", "error", *ITEM_EVENTS, *TERMINALS}
COMPLETED_ONLY_ITEMS = {"agent_message", "reasoning", "error"}
ITEM_TYPES = {
    "agent_message", "reasoning", "command_execution", "file_change",
    "mcp_tool_call", "collab_tool_call", "web_search", "todo_list", "error",
}
USAGE_FIELDS = {
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
}
PROBE_OUTPUT_LIMIT = 16 * 1024
TERMINATE_TIMEOUT = 2.0
PROBE_CANDIDATE_TIMEOUT = 5.0
PROBE_CLEANUP_SLICE = 0.1
CHILD_PATH = "/usr/local/bin:/usr/bin:/bin"
# Linux UAPI values for Python builds that omit memfd/seal constant exports.
MEMFD_CLOEXEC = 0x0001
MEMFD_ALLOW_SEALING = 0x0002
F_ADD_SEALS = 1033
F_SEAL_SEAL = 0x0001
F_SEAL_SHRINK = 0x0002
F_SEAL_GROW = 0x0004
F_SEAL_WRITE = 0x0008


class CodexProvider:
    id = "codex"

    def __init__(self, executable: str = "codex", timeout: float = 300.0):
        resolved = shutil.which(executable)
        self.resolved_path = os.path.realpath(resolved) if resolved else None
        self._fd = _freeze_executable(self.resolved_path)
        self.executable = _fd_path(self._fd)
        self.path = self.resolved_path
        self.timeout = timeout
        self.version: str | None = None
        self.status = _initial_status(resolved, self._fd)
        self.reason = _initial_reason(resolved, self._fd)
        self.last_checked_at = _checked_at()

    @property
    def executable_identity(self) -> str | None:
        return _executable_identity(self._fd)

    @classmethod
    def detected(cls, executable: str = "codex") -> CodexProvider:
        provider = cls(executable)
        if provider.path is None:
            provider.reason = {"code": "not_on_path", "probe": "path"}
            return provider
        if provider._fd is None:
            return provider
        provider.version, provider.status, provider.reason = _version(provider.executable, provider._fd)
        if provider.status == "found":
            provider.status, provider.reason = _readiness(provider.executable, provider._fd)
        return provider

    def close(self) -> None:
        fd, self._fd = self._fd, None
        self.executable = None
        _close_fd(fd)

    def __del__(self):
        try:
            self.close()
        except Exception:
            return

    async def start(self, model: str, context: dict[str, Any]):
        task = asyncio.create_task(self._start(model, context))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            process = await task
            await self.stop(process)
            raise

    async def _start(self, model: str, context: dict[str, Any]):
        if self._fd is None or self.executable is None:
            raise TraceError("cli_unavailable", "frozen codex executable is unavailable")
        try:
            return await asyncio.create_subprocess_exec(
                *self._command(model, context), cwd=context["workspace"],
                env=_environment(context), stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                pass_fds=(self._fd,), **_process_group_options(),
            )
        except OSError:
            raise TraceError("cli_unavailable", "frozen codex executable is unavailable") from None

    async def collect(
        self, process, messages: list[dict], emit: Emit, continuations=()
    ) -> CollectedResult:
        values: list[str] = []
        result = await _collect(
            process, _latest_user(messages), emit, self.timeout, continuations,
            values.append,
        )
        return CollectedResult(result, values[0] if values else None)

    async def stop(self, process) -> None:
        await _bounded_stop(process)

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        options = _options(model, context)
        if session_id := context.get("provider_session_id"):
            return [self.executable, "exec", "resume", *options, session_id, "-"]
        return [self.executable, "exec", *options, "-s", context["sandbox"], "-"]


def _options(model: str, context: dict[str, Any]) -> list[str]:
    return ["--json", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
            "--disable", "shell_tool", "-m", model,
            "-c", f'model_reasoning_effort="{context["reasoning_effort"]}"']


def _environment(context: dict[str, Any]) -> dict[str, str]:
    home = context["codex_home"]
    return {**_probe_environment(), "CODEX_HOME": home, "HOME": home}


def _probe_environment() -> dict[str, str]:
    return {"LANG": "C.UTF-8", "PATH": CHILD_PATH}


def _version(executable: str, fd: int | None) -> tuple[str | None, str, dict[str, str] | None]:
    result = _version_probe(executable, fd)
    if isinstance(result, tuple):
        return result
    if result.returncode != 0:
        return None, "error", _reason("probe_failed", "version")
    match = VERSION.search(result.stdout)
    if match is None:
        return None, "error", _reason("probe_invalid_output", "version")
    return _version_status(match.group(1))


def _version_probe(executable: str, fd: int | None):
    return _probe([executable, "--version"], "version", _probe_environment(), fd)


def _probe(argv: list[str], name: str, environment=None, fd: int | None = None):
    deadline = time.monotonic() + PROBE_CANDIDATE_TIMEOUT
    process = _start_probe(argv, name, environment, fd)
    if isinstance(process, tuple):
        return process
    stdout, stderr = _bounded_probe_output(process)
    return _complete_probe(process, stdout, stderr, deadline, name, argv)


def _start_probe(argv, name, environment, fd):
    try:
        options = {**_process_group_options(), "env": environment}
        if fd is not None:
            options["pass_fds"] = (fd,)
        return subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **options)
    except OSError:
        return None, "error", _reason("probe_failed", name)


def _complete_probe(process, stdout, stderr, deadline, name, argv):
    try:
        process.wait(timeout=_remaining(deadline))
    except subprocess.TimeoutExpired:
        _stop_probe(process, deadline)
        _join_probe_readers(stdout, stderr, deadline=deadline)
        return None, "error", _reason("probe_timeout", name)
    except OSError:
        _join_probe_readers(stdout, stderr, deadline=deadline)
        return None, "error", _reason("probe_failed", name)
    if _reader_cleanup_failed(process, stdout, stderr, deadline):
        return None, "error", _reason("probe_timeout", name)
    return subprocess.CompletedProcess(argv, process.returncode, stdout.value, stderr.value)


def _bounded_probe_output(process):
    stdout, stderr = _ProbeOutput(), _ProbeOutput()
    _start_probe_reader(process.stdout, stdout)
    _start_probe_reader(process.stderr, stderr)
    return stdout, stderr


def _start_probe_reader(stream, output) -> None:
    thread = threading.Thread(target=_drain_probe_stream, args=(stream, output), daemon=True)
    thread.start()
    output.thread = thread


def _drain_probe_stream(stream, output) -> None:
    while chunk := stream.read(4096):
        if len(output.chunks) < PROBE_OUTPUT_LIMIT:
            output.chunks.extend(chunk[:PROBE_OUTPUT_LIMIT - len(output.chunks)])


def _join_probe_readers(*outputs, deadline) -> None:
    for output in outputs:
        output.thread.join(_remaining(deadline))
        output.value = bytes(output.chunks).decode(errors="replace")
    return all(not output.thread.is_alive() for output in outputs)


class _ProbeOutput:
    def __init__(self):
        self.chunks = bytearray()
        self.thread = None
        self.value = ""


def _stop_probe(process, deadline) -> None:
    _terminate_tree(process)
    _kill_tree(process)
    _wait_probe(process, deadline)


def _reader_cleanup_failed(process, stdout, stderr, deadline) -> bool:
    short_deadline = min(deadline, time.monotonic() + PROBE_CLEANUP_SLICE)
    if _join_probe_readers(stdout, stderr, deadline=short_deadline):
        return False
    _stop_probe(process, deadline)
    _join_probe_readers(stdout, stderr, deadline=deadline)
    return True


def _wait_probe(process, deadline) -> bool:
    try:
        process.wait(timeout=min(PROBE_CLEANUP_SLICE, _remaining(deadline)))
    except subprocess.TimeoutExpired:
        return False
    return process.returncode is not None


def _remaining(deadline) -> float:
    return max(0.0, deadline - time.monotonic())


def _version_status(version: str) -> tuple[str, str, dict[str, str] | None]:
    if version == COMPATIBLE_VERSION:
        return version, "found", None
    return version, "unsupported", _reason("version_incompatible", "version")


async def _collect(
    process, prompt: str, emit: Emit, timeout: float, continuations=(), on_continuation=None
) -> ModelResult:
    try:
        stdout = await _stdout(process, prompt, timeout)
        events = _events(stdout)
    except TraceError as error:
        _redact_failed_stream(error, continuations)
        raise
    thread_id = _thread_id(events)
    ids = _continuation_ids(events, continuations)
    events = _redact_threads(events, ids)
    text = _agent_text(events)
    if text:
        await emit(text)
    if on_continuation is not None and thread_id:
        on_continuation(thread_id)
    return ModelResult({"role": "assistant", "content": text}, _usage(events),
                       _trace_items(events))


def _redact_failed_stream(error, continuations) -> None:
    items = getattr(error, "provider_items", [])
    ids = _continuation_ids(items, continuations, getattr(error, "continuation_id", None))
    error.provider_items = _redact_threads(items, ids)
    if terminal := getattr(error, "provider_terminal", None):
        error.provider_terminal = _redact_threads(terminal, ids)
    error.continuation_ids = ids


def _continuation_ids(events, known=(), thread_id=None) -> tuple[str, ...]:
    values = [value for value in (*known, thread_id) if value]
    for event in events:
        item = event.get("item", event) if isinstance(event, dict) else {}
        if isinstance(event, dict) and event.get("type") == "thread.started":
            values.append(event["thread_id"])
        if isinstance(item, dict) and item.get("type") == "collab_tool_call":
            values.extend(_collab_continuations(item))
    return tuple(dict.fromkeys(values))


def _collab_continuations(item) -> list[str]:
    values = [item["sender_thread_id"], *item["receiver_thread_ids"]]
    for key in item["agents_states"]:
        values.append(key)
    return values


def _redact_threads(value, thread_ids):
    ids = tuple(thread_id for thread_id in thread_ids if thread_id)
    if not ids:
        return value
    if isinstance(value, dict):
        return _redact_thread_mapping(value, ids)
    if isinstance(value, list):
        return [_redact_threads(item, ids) for item in value]
    return _redact_text(value, ids) if isinstance(value, str) else value


def _redact_thread_mapping(value, thread_ids):
    redacted = {}
    for key, item in value.items():
        redacted[_unique_key(redacted, _redact_thread_key(key, thread_ids))] = _redact_threads(item, thread_ids)
    return redacted


def _redact_thread_key(key, thread_ids):
    return "<redacted>" if key in thread_ids else key


def _unique_key(value, key):
    index, candidate = 2, key
    while candidate in value:
        candidate = f"{key}#{index}"
        index += 1
    return candidate


def _redact_text(value, thread_ids):
    for thread_id in thread_ids:
        if value == thread_id:
            return "<redacted>"
        value = re.sub(
            rf"(?<!\w){re.escape(thread_id)}(?!\w)", "<redacted>", value
        )
    return value


async def _stdout(process, prompt: str, timeout: float) -> bytes:
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(prompt.encode()), timeout
        )
    except TimeoutError as error:
        await _stop_after_timeout(process)
        raise TraceError(
            "cli_timeout", f"codex timed out after {timeout:g}s"
        ) from error
    if process.returncode:
        raise TraceError("cli_failed", f"codex exited {process.returncode}")
    return stdout


async def _stop_after_timeout(process) -> None:
    await _bounded_stop(process)


async def _wait(process) -> bool:
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
    except TimeoutError:
        return False
    return process.returncode is not None


async def _bounded_stop(process) -> None:
    _terminate_tree(process)
    await asyncio.sleep(TERMINATE_TIMEOUT)
    _kill_tree(process)
    if not await _wait(process):
        raise TraceError("cli_termination_timeout", "codex did not terminate")


def _process_group_options() -> dict[str, int | bool]:
    if os.name == "posix":
        return {"start_new_session": True}
    return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}


def _terminate_tree(process) -> None:
    _signal_tree(process, signal.SIGTERM, "terminate", force=True)


def _kill_tree(process) -> None:
    if os.name == "nt":
        _taskkill(process)
        return
    _signal_tree(process, signal.SIGKILL, "kill", force=True)


def _signal_tree(process, sig, fallback: str, force: bool = False) -> None:
    if process.returncode is not None and not force:
        return
    if os.name == "posix" and getattr(process, "pid", None):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        return
    if os.name == "nt" and getattr(process, "pid", None):
        _taskkill(process)
        return
    getattr(process, fallback)()


def _taskkill(process) -> None:
    if process.returncode is None and getattr(process, "pid", None):
        _run_taskkill(process.pid)


def _run_taskkill(pid: int) -> None:
    try:
        subprocess.run(_taskkill_args(pid), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False, timeout=TERMINATE_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return


def _taskkill_args(pid: int) -> list[str]:
    return ["taskkill", "/PID", str(pid), "/T", "/F"]


def _events(stdout: bytes) -> list[dict]:
    try:
        values = [
            json.loads(line) for line in stdout.decode().splitlines() if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _invalid_jsonl() from error
    if not values or not all(_valid_shape(item) for item in values):
        raise _invalid_jsonl()
    _validate_stream(values)
    return values


def _invalid_jsonl() -> TraceError:
    return TraceError("cli_invalid_jsonl", "codex returned invalid JSONL")


def _validate_stream(events: list[dict]) -> None:
    terminal = _Lifecycle().consume(events)
    if terminal == "turn.completed":
        return
    if terminal == "turn.failed":
        error = TraceError("cli_stream_failed", "codex returned a failed terminal stream")
        error.provider_items, error.provider_terminal = _trace_items(events), _terminal(events)
        error.continuation_id = _thread_id(events)
        raise error
    raise TraceError(
        "cli_incomplete_stream", "codex returned an incomplete terminal stream"
    )


class _Lifecycle:
    def __init__(self):
        self.state = "new"
        self.items: dict[str, tuple[str, str]] = {}
        self.failed = False

    def consume(self, events: list[dict]) -> str:
        for event in events:
            self._event(event)
        if self.state not in TERMINALS:
            raise _incomplete()
        return self.state

    def _event(self, event: dict) -> None:
        kind = event["type"]
        if kind in {"thread.started", "turn.started"}:
            self._start(kind)
        elif kind in TERMINALS:
            self._terminal(kind)
        elif kind == "error":
            self._error()
        else:
            self._item(kind, event["item"])

    def _start(self, kind: str) -> None:
        expected = {"new": "thread.started", "thread.started": "turn.started"}.get(self.state)
        if kind != expected:
            raise _invalid_jsonl()
        self.state = kind

    def _item(self, kind: str, item: dict) -> None:
        if self.state != "turn.started":
            raise _invalid_jsonl()
        item_id, item_type = item["id"], item["type"]
        previous = self.items.get(item_id)
        if previous is not None and previous[1] != item_type:
            raise _invalid_jsonl()
        if not _phase_matches(kind, item):
            raise _invalid_jsonl()
        self._advance_item(kind, item_id, item_type, previous)

    def _advance_item(self, kind, item_id, item_type, previous) -> None:
        state = previous[0] if previous else None
        if kind == "item.started" and _starts_item(item_type, state):
            self.items[item_id] = ("started", item_type)
        elif kind == "item.updated" and _may_update(state, item_type):
            self.items[item_id] = ("updated", item_type)
        elif kind == "item.completed" and self._completable(state, item_type):
            self.items[item_id] = ("completed", item_type)
        else:
            raise _invalid_jsonl()

    def _completable(self, state, item_type) -> bool:
        if item_type == "file_change":
            return state is None
        return state in {"started", "updated"} or (
            state is None and item_type in COMPLETED_ONLY_ITEMS
        )

    def _error(self) -> None:
        if self.state != "turn.started":
            raise _invalid_jsonl()
        self.failed = True

    def _terminal(self, kind: str) -> None:
        complete = all(value[0] == "completed" for value in self.items.values())
        if self.state != "turn.started" or not complete:
            raise _invalid_jsonl()
        if self.failed and kind != "turn.failed":
            raise _invalid_jsonl()
        self.state = kind


def _incomplete() -> TraceError:
    return TraceError("cli_incomplete_stream", "codex returned an incomplete terminal stream")


def _valid_shape(event: object) -> bool:
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        return False
    kind = event["type"]
    if kind not in EVENTS:
        return False
    if kind == "thread.started":
        return _valid_thread(event)
    if kind == "turn.started":
        return _exact(event, {"type"})
    if kind in ITEM_EVENTS:
        return _valid_item(event)
    if kind == "turn.completed":
        return _valid_usage(event)
    if kind == "turn.failed":
        return _valid_terminal(event)
    return _valid_error(event)


def _valid_thread(event: dict) -> bool:
    return _exact(event, {"type", "thread_id"}) and isinstance(event["thread_id"], str) and bool(event["thread_id"].strip())


def _valid_item(event: dict) -> bool:
    item = event.get("item")
    if not _exact(event, {"type", "item"}) or not _item_identity(item):
        return False
    if item.get("type") not in ITEM_TYPES:
        return False
    return _valid_item_payload(item)


def _valid_item_payload(item: dict) -> bool:
    validators = {
        "agent_message": _text_item, "reasoning": _text_item,
        "error": _message_item, "command_execution": _command_item,
        "file_change": _file_item, "mcp_tool_call": _mcp_item,
        "collab_tool_call": _collab_item, "web_search": _web_item,
        "todo_list": _todo_item,
    }
    return validators[item["type"]](item)


def _item_identity(item: object) -> bool:
    return isinstance(item, dict) and isinstance(item.get("id"), str) and bool(item["id"].strip())


def _may_update(state, item_type) -> bool:
    return state in {"started", "updated"} and item_type == "todo_list"


def _starts_item(item_type, state) -> bool:
    return state is None and item_type != "file_change" and item_type not in COMPLETED_ONLY_ITEMS


def _phase_matches(kind, item) -> bool:
    status = item.get("status")
    if status is None:
        return True
    return (kind == "item.started" and status == "in_progress") or (
        kind == "item.completed" and status != "in_progress"
    )


def _text_item(item: dict) -> bool:
    return _exact(item, {"id", "type", "text"}) and isinstance(item["text"], str)


def _message_item(item: dict) -> bool:
    return _exact(item, {"id", "type", "message"}) and isinstance(item["message"], str)


def _command_item(item: dict) -> bool:
    fields = {"id", "type", "command", "aggregated_output", "exit_code", "status"}
    return _exact(item, fields) and _command_values(item)


def _command_values(item: dict) -> bool:
    return (isinstance(item["command"], str) and isinstance(item["aggregated_output"], str)
            and _integer_or_none(item["exit_code"])
            and item["status"] in {"in_progress", "completed", "failed", "declined"})


def _file_item(item: dict) -> bool:
    return _exact(item, {"id", "type", "changes", "status"}) and _changes(item["changes"]) and item["status"] in {"in_progress", "completed", "failed"}


def _changes(value) -> bool:
    return isinstance(value, list) and all(_change(item) for item in value)


def _change(value) -> bool:
    return isinstance(value, dict) and _exact(value, {"path", "kind"}) and isinstance(value["path"], str) and value["kind"] in {"add", "delete", "update"}


def _mcp_item(item: dict) -> bool:
    fields = {"id", "type", "server", "tool", "arguments", "result", "error", "status"}
    return _exact(item, fields) and _mcp_values(item)


def _mcp_values(item: dict) -> bool:
    return (isinstance(item["server"], str) and isinstance(item["tool"], str)
            and _json_value(item["arguments"]) and _mcp_result(item["result"])
            and _mcp_error(item["error"]) and item["status"] in {"in_progress", "completed", "failed"})


def _mcp_result(value) -> bool:
    return value is None or (isinstance(value, dict) and _result_fields(value)
                             and isinstance(value["content"], list)
                             and _json_value(value.get("_meta"))
                             and _json_value(value["structured_content"]))


def _result_fields(value) -> bool:
    return set(value) in ({"content", "structured_content"}, {"content", "_meta", "structured_content"})


def _mcp_error(value) -> bool:
    return value is None or (isinstance(value, dict) and _exact(value, {"message"}) and isinstance(value["message"], str))


def _collab_item(item: dict) -> bool:
    fields = {"id", "type", "tool", "sender_thread_id", "receiver_thread_ids", "prompt", "agents_states", "status"}
    return _exact(item, fields) and _collab_values(item)


def _collab_values(item: dict) -> bool:
    return (item["tool"] in {"spawn_agent", "send_input", "wait", "close_agent"}
            and isinstance(item["sender_thread_id"], str) and _strings(item["receiver_thread_ids"])
            and _string_or_none(item["prompt"]) and _agent_states(item["agents_states"])
            and item["status"] in {"in_progress", "completed", "failed"})


def _agent_states(value) -> bool:
    return isinstance(value, dict) and all(_agent_state(item) for item in value.values())


def _agent_state(value) -> bool:
    return isinstance(value, dict) and _exact(value, {"status", "message"}) and value["status"] in {"pending_init", "running", "interrupted", "completed", "errored", "shutdown", "not_found"} and _string_or_none(value["message"])


def _web_item(item: dict) -> bool:
    return _exact(item, {"id", "type", "query", "action"}) and isinstance(item["query"], str) and _web_action(item)


def _web_action(item) -> bool:
    action = item["action"]
    if not isinstance(action, dict) or action.get("type") != "search":
        return False
    if set(action) not in ({"type", "query"}, {"type", "query", "queries"}):
        return False
    return action["query"] == item["query"] and _same_queries(action, item["query"])


def _same_queries(action, query) -> bool:
    queries = action.get("queries", [query])
    return isinstance(query, str) and _strings(queries) and all(value == query for value in queries)


def _todo_item(item: dict) -> bool:
    return _exact(item, {"id", "type", "items"}) and isinstance(item["items"], list) and all(_todo(value) for value in item["items"])


def _todo(value) -> bool:
    return isinstance(value, dict) and _exact(value, {"text", "completed"}) and isinstance(value["text"], str) and isinstance(value["completed"], bool)


def _exact(value, fields) -> bool:
    return set(value) == fields


def _integer_or_none(value) -> bool:
    return value is None or _integer(value)


def _integer(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _string_or_none(value) -> bool:
    return value is None or isinstance(value, str)


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _strings_or_none(value) -> bool:
    return value is None or _strings(value)


def _json_value(value) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def _valid_usage(event: dict) -> bool:
    usage = event.get("usage")
    return _exact(event, {"type", "usage"}) and isinstance(usage, dict) and set(usage) == USAGE_FIELDS and all(
        _token_count(value) for value in usage.values()
    )


def _valid_terminal(event: dict) -> bool:
    error = event.get("error")
    return _exact(event, {"type", "error"}) and _message(error)


def _valid_error(event: dict) -> bool:
    return _exact(event, {"type", "message"}) and isinstance(event["message"], str)


def _message(value) -> bool:
    return isinstance(value, dict) and _exact(value, {"message"}) and isinstance(value["message"], str)


def _checked_at() -> str:
    return datetime.now(UTC).isoformat()


def _reason(code: str, probe: str) -> dict[str, str]:
    return {"code": code, "probe": probe}


def _token_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _trace_items(events: list[dict]) -> list[dict]:
    return [_trace_item(event) for event in events if event["type"] in ITEM_EVENTS]


def _terminal(events: list[dict]) -> dict:
    event = next(item for item in reversed(events) if item["type"] in TERMINALS)
    return {"phase": event["type"].split(".")[1], "error": event.get("error")}


def _trace_item(event: dict) -> dict:
    return {"phase": event["type"].split(".")[1], "item": _safe(event["item"])}


def _safe(value):
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items() if not _sensitive(key)}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def _sensitive(key: str) -> bool:
    value = key.lower().replace("_", "")
    return any(token in value for token in ("token", "secret", "password", "authorization", "apikey"))


def _initial_status(resolved, fd) -> str:
    if resolved is None:
        return "missing"
    if fd is not None:
        return "found"
    return "error" if _snapshot_supported() else "unsupported"


def _initial_reason(resolved, fd) -> dict[str, str] | None:
    if resolved is None or fd is not None:
        return None
    code = "snapshot_unavailable" if _snapshot_supported() else "unsupported_platform"
    return _reason(code, "snapshot")


def _freeze_executable(path: str | None) -> int | None:
    source = _open_source(path)
    if source is None:
        return None
    try:
        return _sealed_snapshot(source)
    except OSError:
        return None
    finally:
        _close_fd(source)


def _open_source(path: str | None) -> int | None:
    if path is None or not _snapshot_supported():
        return None
    try:
        return os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    except OSError:
        return None


def _snapshot_supported() -> bool:
    return (sys.platform == "linux" and platform.machine() in {"x86_64", "amd64", "AMD64"}
            and fcntl is not None)


def _sealed_snapshot(source: int) -> int:
    snapshot = _memfd_create()
    try:
        _copy_fd(source, snapshot)
        os.fchmod(snapshot, 0o500)
        _seal_snapshot(snapshot)
        return snapshot
    except OSError:
        _close_fd(snapshot)
        raise


def _memfd_flags() -> int:
    return MEMFD_CLOEXEC | MEMFD_ALLOW_SEALING


def _memfd_create() -> int:
    if hasattr(os, "memfd_create"):
        return os.memfd_create("codex-snapshot", _memfd_flags())
    return _libc_memfd_create()


def _libc_memfd_create() -> int:
    library = ctypes.CDLL(None, use_errno=True)
    create = getattr(library, "memfd_create", None)
    if create is None:
        raise OSError("memfd_create")
    create.argtypes, create.restype = (ctypes.c_char_p, ctypes.c_uint), ctypes.c_int
    descriptor = create(b"codex-snapshot", _memfd_flags())
    if descriptor == -1:
        raise OSError(ctypes.get_errno(), "memfd_create")
    return descriptor


def _copy_fd(source: int, target: int) -> None:
    while chunk := os.read(source, 1024 * 1024):
        _write_fd(target, chunk)


def _write_fd(target: int, chunk: bytes) -> None:
    while chunk:
        written = os.write(target, chunk)
        chunk = chunk[written:]


def _seal_snapshot(snapshot: int) -> None:
    fcntl.fcntl(snapshot, F_ADD_SEALS, _seal_flags())


def _seal_flags() -> int:
    return F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE


def _close_fd(fd: int | None) -> None:
    if fd is None:
        return
    try:
        os.close(fd)
    except OSError:
        return


def _fd_path(fd: int | None) -> str | None:
    return f"/proc/self/fd/{fd}" if fd is not None else None


def _executable_identity(fd: int | None) -> str | None:
    if fd is None:
        return None
    try:
        with os.fdopen(os.dup(fd), "rb") as executable:
            executable.seek(0)
            return hashlib.file_digest(executable, "sha256").hexdigest()
    except OSError:
        return None


def _latest_user(messages: list[dict]) -> str:
    system = next(
        (item["content"] for item in messages if item["role"] == "system"), ""
    )
    user = next(
        (item["content"] for item in reversed(messages) if item["role"] == "user"), ""
    )
    return f"{system}\n\n{user}" if len(messages) <= 2 else user


def _agent_text(events: list[dict]) -> str:
    values = [item["item"]["text"] for item in events if _agent_message(item)]
    return "\n".join(value for value in values if value)


def _agent_message(event: dict) -> bool:
    return (
        event["type"] == "item.completed" and event["item"]["type"] == "agent_message"
    )


def _thread_id(events: list[dict]) -> str | None:
    event = next((item for item in events if item["type"] == "thread.started"), None)
    return event["thread_id"] if event else None


def _usage(events: list[dict]) -> dict[str, int]:
    event = next(item for item in reversed(events) if item["type"] == "turn.completed")
    usage = event["usage"]
    return usage


def _readiness(executable: str, fd: int | None) -> tuple[str, dict[str, str] | None]:
    with tempfile.TemporaryDirectory() as home:
        try:
            prepare_session_auth(Path(home))
        except RuntimeError:
            return "auth-required", {"code": "auth_missing", "probe": "login status"}
        result = _probe([executable, "login", "status"], "login status", _environment({"codex_home": home}), fd)
    if isinstance(result, tuple):
        _, status, reason = result
        return ("found", _reason("auth_probe_unavailable", "login status")) if reason["code"] == "probe_failed" else (status, reason)
    if result.returncode == 0:
        return "ready", None
    return "auth-required", {"code": "auth_missing", "probe": "login status"}

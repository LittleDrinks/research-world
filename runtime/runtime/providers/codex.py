from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
from datetime import UTC, datetime
from typing import Any

from .base import Emit, ModelResult
from ..types import TraceError

VERSION = re.compile(r"codex-cli\s+(\S+)")
COMPATIBLE_VERSION = "0.149.1"
TERMINALS = {"turn.completed", "turn.failed"}
ITEM_EVENTS = {"item.started", "item.updated", "item.completed"}
EVENTS = {"thread.started", "turn.started", "error", *ITEM_EVENTS, *TERMINALS}
COMPLETED_ONLY_ITEMS = {"agent_message", "reasoning", "error", "file_change"}
TERMINATE_TIMEOUT = 2.0


class CodexProvider:
    id = "codex"

    def __init__(self, executable: str = "codex", timeout: float = 300.0):
        resolved = shutil.which(executable)
        self.executable = resolved or executable
        self.path = resolved
        self.resolved_path = os.path.realpath(resolved) if resolved else None
        self.timeout = timeout
        self.version: str | None = None
        self.status = "ready" if resolved else "missing"
        self.reason: dict[str, str] | None = None
        self.last_checked_at = _checked_at()

    @classmethod
    def detected(cls) -> CodexProvider:
        provider = cls()
        if provider.path is None:
            provider.reason = {"code": "not_on_path", "probe": "path"}
            return provider
        provider.version, provider.status, provider.reason = _version(provider.path)
        if provider.status == "found":
            provider.status, provider.reason = _readiness(provider.path)
        return provider

    async def start(self, model: str, context: dict[str, Any]):
        task = asyncio.create_task(self._start(model, context))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            process = await task
            await self.stop(process)
            raise

    async def _start(self, model: str, context: dict[str, Any]):
        return await asyncio.create_subprocess_exec(
            *self._command(model, context),
            cwd=context["workspace"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **_process_group_options(),
        )

    async def collect(self, process, messages: list[dict], emit: Emit) -> ModelResult:
        return await _collect(process, _latest_user(messages), emit, self.timeout)

    def cancel(self, process) -> None:
        _terminate_tree(process)

    async def stop(self, process) -> None:
        self.cancel(process)
        if await _wait(process):
            return
        _kill_tree(process)
        if not await _wait(process):
            raise TraceError("cli_termination_timeout", "codex did not terminate")

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        options = ["--json", "--skip-git-repo-check", "-m", model]
        options += ["-c", f'model_reasoning_effort="{context["reasoning_effort"]}"']
        if session_id := context.get("provider_session_id"):
            return [self.executable, "exec", "resume", *options, session_id, "-"]
        return [self.executable, "exec", *options, "-s", context["sandbox"], "-"]


def _version(executable: str) -> tuple[str | None, str, dict[str, str] | None]:
    result = _version_probe(executable)
    if isinstance(result, tuple):
        return result
    match = VERSION.search(result.stdout) if result.returncode == 0 else None
    if match is None:
        return None, "error", _reason("probe_invalid_output", "version")
    return _version_status(match.group(1))


def _version_probe(executable: str):
    try:
        return subprocess.run(
            [executable, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except subprocess.TimeoutExpired:
        return None, "error", _reason("probe_timeout", "version")
    except OSError:
        return None, "error", _reason("probe_failed", "version")


def _version_status(version: str) -> tuple[str, str, dict[str, str] | None]:
    if version == COMPATIBLE_VERSION:
        return version, "found", None
    return version, "unsupported", _reason("version_incompatible", "version")


async def _collect(process, prompt: str, emit: Emit, timeout: float) -> ModelResult:
    stdout = await _stdout(process, prompt, timeout)
    events = _events(stdout)
    text = _agent_text(events)
    if text:
        await emit(text)
    return ModelResult(
        {"role": "assistant", "content": text}, _usage(events), _thread_id(events)
    )


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
    _kill_tree(process)
    if not await _wait(process):
        raise TraceError("cli_termination_timeout", "codex did not terminate")


async def _wait(process) -> bool:
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
    except TimeoutError:
        return False
    return process.returncode is not None


def _process_group_options() -> dict[str, int | bool]:
    if os.name == "posix":
        return {"start_new_session": True}
    return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}


def _terminate_tree(process) -> None:
    _signal_tree(process, signal.SIGTERM, "terminate")


def _kill_tree(process) -> None:
    if os.name == "nt":
        _taskkill(process)
        return
    _signal_tree(process, signal.SIGKILL, "kill")


def _signal_tree(process, sig, fallback: str) -> None:
    if process.returncode is not None:
        return
    if os.name == "posix" and getattr(process, "pid", None):
        os.killpg(os.getpgid(process.pid), sig)
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
        raise TraceError("cli_stream_failed", "codex returned a failed terminal stream")
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
        expected = "thread.started" if self.state == "new" else "turn.started"
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
        self._advance_item(kind, item_id, item_type, previous)

    def _advance_item(self, kind, item_id, item_type, previous) -> None:
        state = previous[0] if previous else None
        if kind == "item.started" and state is None:
            self.items[item_id] = ("started", item_type)
        elif kind == "item.updated" and state in {"started", "updated"}:
            self.items[item_id] = ("updated", item_type)
        elif kind == "item.completed" and self._completable(state, item_type):
            self.items[item_id] = ("completed", item_type)
        else:
            raise _invalid_jsonl()

    def _completable(self, state, item_type) -> bool:
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
        return True
    if kind in ITEM_EVENTS:
        return _valid_item(event)
    if kind == "turn.completed":
        return _valid_usage(event)
    if kind == "turn.failed":
        return _valid_terminal(event)
    return _valid_error(event)


def _valid_thread(event: dict) -> bool:
    return isinstance(event.get("thread_id"), str) and bool(event["thread_id"].strip())


def _valid_item(event: dict) -> bool:
    item = event.get("item")
    if not _item_identity(item) or not isinstance(item.get("type"), str):
        return False
    return _item_text_is_valid(event["type"], item)


def _item_text_is_valid(kind: str, item: dict) -> bool:
    return kind != "item.completed" or item["type"] != "agent_message" or isinstance(item.get("text"), str)


def _item_identity(item: object) -> bool:
    return isinstance(item, dict) and isinstance(item.get("id"), str) and bool(item["id"].strip())


def _valid_usage(event: dict) -> bool:
    usage = event.get("usage", {})
    if not isinstance(usage, dict):
        return False
    return all(
        _token_count(usage.get(key, 0)) for key in ("input_tokens", "output_tokens")
    )


def _valid_terminal(event: dict) -> bool:
    error = event.get("error")
    return isinstance(error, dict) and isinstance(error.get("message"), str)


def _valid_error(event: dict) -> bool:
    return isinstance(event.get("message"), str)


def _checked_at() -> str:
    return datetime.now(UTC).isoformat()


def _reason(code: str, probe: str) -> dict[str, str]:
    return {"code": code, "probe": probe}


def _token_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


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
    usage = event.get("usage", {})
    return {
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
    }


def _readiness(executable: str) -> tuple[str, dict[str, str] | None]:
    try:
        result = subprocess.run(
            [executable, "login", "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except FileNotFoundError:
        return "found", {"code": "auth_probe_unavailable", "probe": "login status"}
    except subprocess.TimeoutExpired:
        return "error", {"code": "probe_timeout", "probe": "login status"}
    except OSError:
        return "error", {"code": "probe_failed", "probe": "login status"}
    if result.returncode == 0:
        return "ready", None
    return "auth-required", {"code": "auth_missing", "probe": "login status"}

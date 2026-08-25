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
TERMINALS = {"turn.completed", "turn.failed", "turn.cancelled"}
EVENTS = {"thread.started", "turn.started", "item.started", "item.updated", "item.completed", *TERMINALS}


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
        await process.wait()

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        options = ["--json", "--skip-git-repo-check", "-m", model]
        options += ["-c", f'model_reasoning_effort="{context["reasoning_effort"]}"']
        if session_id := context.get("provider_session_id"):
            return [self.executable, "exec", "resume", *options, session_id, "-"]
        return [self.executable, "exec", *options, "-s", context["sandbox"], "-"]


def _version(executable: str) -> tuple[str | None, str, dict[str, str] | None]:
    try:
        result = subprocess.run(
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
    match = VERSION.search(result.stdout) if result.returncode == 0 else None
    if match:
        return match.group(1), "found", None
    return None, "error", _reason("probe_invalid_output", "version")


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
        _kill_tree(process)
        await process.wait()
        raise TraceError(
            "cli_timeout", f"codex timed out after {timeout:g}s"
        ) from error
    if process.returncode:
        raise TraceError("cli_failed", f"codex exited {process.returncode}")
    return stdout


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
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


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
    terminal = _stream_state(events)
    if terminal == "turn.completed":
        return
    if terminal in {"turn.failed", "turn.cancelled"}:
        raise TraceError("cli_stream_failed", "codex returned a failed terminal stream")
    raise TraceError(
        "cli_incomplete_stream", "codex returned an incomplete terminal stream"
    )


def _stream_state(events: list[dict]) -> str:
    state = "new"
    for event in events:
        state = _next_state(state, event["type"])
    if state not in TERMINALS:
        raise TraceError("cli_incomplete_stream", "codex returned an incomplete terminal stream")
    return state


def _next_state(state: str, kind: str) -> str:
    allowed = {"new": {"thread.started"}, "thread.started": {"turn.started"}, "turn.started": EVENTS - {"thread.started", "turn.started"}}
    if kind not in allowed.get(state, set()):
        raise _invalid_jsonl()
    return kind if kind in {"thread.started", "turn.started", *TERMINALS} else state


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
    if kind in {"item.started", "item.updated", "item.completed"}:
        return _valid_item(event)
    if kind == "turn.completed":
        return _valid_usage(event)
    return _valid_terminal(event) if kind in TERMINALS else False


def _valid_thread(event: dict) -> bool:
    return isinstance(event.get("thread_id"), str) and bool(event["thread_id"].strip())


def _valid_item(event: dict) -> bool:
    item = event.get("item")
    if not isinstance(item, dict) or not isinstance(item.get("type"), str):
        return False
    return item["type"] != "agent_message" or isinstance(item.get("text"), str)


def _valid_usage(event: dict) -> bool:
    usage = event.get("usage", {})
    if not isinstance(usage, dict):
        return False
    return all(
        _token_count(usage.get(key, 0)) for key in ("input_tokens", "output_tokens")
    )


def _valid_terminal(event: dict) -> bool:
    if event["type"] == "turn.completed":
        return _valid_usage(event)
    error = event.get("error")
    if event["type"] == "turn.cancelled" and error is None:
        return True
    return isinstance(error, dict) and isinstance(error.get("message"), str)


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

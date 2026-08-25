from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
from typing import Any

from .base import Emit, ModelResult
from ..types import TraceError

VERSION = re.compile(r"codex-cli\s+(\S+)")
TERMINALS = {"turn.completed", "turn.failed", "turn.cancelled"}


class CodexProvider:
    id = "codex"

    def __init__(self, executable: str = "codex", timeout: float = 300.0):
        resolved = shutil.which(executable)
        if not resolved:
            raise RuntimeError("codex executable not found")
        self.executable = resolved
        self.timeout = timeout
        self.version: str | None = None
        self.status = "ready"
        self.reason: dict[str, str] | None = None

    @classmethod
    def detected(cls) -> CodexProvider | None:
        executable = shutil.which("codex")
        version = _version(executable) if executable else None
        if version is None:
            return None
        provider = cls(executable)
        provider.version = version
        provider.status, provider.reason = _readiness(executable)
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

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        options = ["--json", "--skip-git-repo-check", "-m", model]
        options += ["-c", f'model_reasoning_effort="{context["reasoning_effort"]}"']
        if session_id := context.get("provider_session_id"):
            return [self.executable, "exec", "resume", *options, session_id, "-"]
        return [self.executable, "exec", *options, "-s", context["sandbox"], "-"]


def _version(executable: str | None) -> str | None:
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = VERSION.search(result.stdout) if result.returncode == 0 else None
    return match.group(1) if match else None


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
    if not values or not all(_valid_event(item) for item in values):
        raise _invalid_jsonl()
    _validate_stream(values)
    return values


def _invalid_jsonl() -> TraceError:
    return TraceError("cli_invalid_jsonl", "codex returned invalid JSONL")


def _validate_stream(events: list[dict]) -> None:
    _validate_thread(events)
    terminal = _stream_terminal(events)
    if terminal == "turn.completed":
        return
    if terminal in {"turn.failed", "turn.cancelled"}:
        raise TraceError("cli_stream_failed", "codex returned a failed terminal stream")
    raise TraceError(
        "cli_incomplete_stream", "codex returned an incomplete terminal stream"
    )


def _validate_thread(events: list[dict]) -> None:
    threads = [item for item in events if item["type"] == "thread.started"]
    if len(threads) != 1 or not _valid_thread(threads[0]):
        raise _invalid_jsonl()


def _stream_terminal(events: list[dict]) -> str | None:
    terminals = [index for index, item in enumerate(events) if item["type"] in TERMINALS]
    if len(terminals) != 1 or terminals[0] != len(events) - 1:
        raise _invalid_jsonl()
    return events[terminals[0]]["type"]


def _valid_event(event: object) -> bool:
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        return False
    kind = event["type"]
    if kind == "thread.started":
        return _valid_thread(event)
    if kind == "item.completed":
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

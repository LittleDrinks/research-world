from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import CollectedResult, Emit, ModelResult
from ..types import TraceError

COMPATIBLE_VERSION = "0.84.3"
VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
CHILD_PATH = "/usr/local/bin:/usr/bin:/bin"
PROMPT_ID = "prompt-1"
PROBE_TIMEOUT = 5.0
TERMINATE_TIMEOUT = 2.0
USAGE_FIELDS = {
    "input_tokens": "input",
    "cached_input_tokens": "cacheRead",
    "cache_write_input_tokens": "cacheWrite",
    "output_tokens": "output",
    "reasoning_output_tokens": "reasoning",
}


class PiProvider:
    id = "pi"

    def __init__(self, executable: str = "pi", timeout: float = 300.0):
        resolved = shutil.which(executable)
        self.resolved_path = os.path.realpath(resolved) if resolved else None
        self.executable = self.resolved_path
        self.path = self.resolved_path
        self.timeout = timeout
        self.version: str | None = None
        self.status = "found" if resolved else "missing"
        self.reason = None if resolved else _reason("not_on_path", "path")
        self.last_checked_at = _checked_at()

    @property
    def executable_identity(self) -> str | None:
        return _executable_identity(self.resolved_path)

    @classmethod
    def detected(cls, executable: str = "pi") -> PiProvider:
        provider = cls(executable)
        if provider.executable is None:
            return provider
        provider._probe_version()
        return provider

    def _probe_version(self) -> None:
        try:
            result = _version_probe(self.executable)
        except subprocess.TimeoutExpired:
            self.status, self.reason = "error", _reason("probe_timeout", "version")
            return
        except OSError:
            self.status, self.reason = "error", _reason("probe_failed", "version")
            return
        self._apply_version(result)

    def _apply_version(self, result) -> None:
        value = result.stdout.strip()
        if result.returncode != 0:
            self.status, self.reason = "error", _reason("probe_failed", "version")
        elif not VERSION.fullmatch(value):
            self.status, self.reason = "error", _reason("probe_invalid_output", "version")
        elif value != COMPATIBLE_VERSION:
            self.version = value
            self.status, self.reason = "incompatible", _reason("version_incompatible", "version")
        else:
            self.version, self.status, self.reason = value, "ready", None

    async def start(
        self, model: str, context: dict[str, Any], messages: list[dict] | None = None
    ):
        if self.executable is None or self.executable_identity is None:
            raise TraceError("pi_unavailable", "pi executable is unavailable")
        try:
            process = await asyncio.create_subprocess_exec(
                *self._command(model, context, messages),
                cwd=context["workspace"], env=_environment(),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, **_process_group_options(),
            )
        except OSError as error:
            raise TraceError("pi_unavailable", "pi executable is unavailable") from error
        process.runtime_session_id = context["runtime_session_id"]
        return process

    def _command(self, model, context, messages=None) -> list[str]:
        command = [
            self.executable, "--mode", "rpc", "--session-id",
            context["runtime_session_id"], "--offline", "--no-approve",
        ]
        command.extend(_model_option(model))
        command.extend(_named_option(context))
        command.extend(_system_option(messages or [], context))
        command.extend(_runtime_options(context))
        return command

    async def collect(
        self, process, messages: list[dict], emit: Emit, continuations=()
    ) -> CollectedResult:
        session_id = _session_id(process, continuations)
        try:
            result = await _collect(process, _latest_user(messages), emit, self.timeout)
        except TraceError as error:
            error.continuation_ids = (session_id,) if session_id else ()
            raise
        return CollectedResult(result, session_id)

    async def stop(self, process) -> None:
        await _send_abort(process)
        _close_stdin(process)
        await _bounded_stop(process)
        await _finish_stderr(process)

    def close(self) -> None:
        return None


class PiEventParser:
    def __init__(self):
        self.acknowledged = False
        self.terminal = False
        self.text = ""
        self.items: list[dict[str, Any]] = []
        self.usage = _empty_usage()
        self._message_index = 0
        self._thinking: dict[tuple[int, int], str] = {}

    def consume(self, event: dict[str, Any]) -> str | None:
        kind = _event_type(event)
        if kind == "response":
            self._response(event)
        elif kind == "message_start":
            self._message_start(event)
        elif kind == "message_update":
            return self._message_update(event)
        elif kind == "message_end":
            self._message_end(event)
        elif kind.startswith("tool_execution_"):
            self._tool(event)
        elif kind == "agent_end":
            self._agent_end(event)
        else:
            self._auxiliary(kind, event)
        return None

    def _auxiliary(self, kind, event) -> None:
        if kind == "extension_error":
            raise _error("pi_extension_error", "pi extension failed")
        if kind == "auto_retry_end" and event.get("success") is False:
            raise _error("pi_retry_exhausted", "pi exhausted automatic retries")
        if kind == "extension_ui_request":
            self._extension_ui(event)

    def _response(self, event) -> None:
        if event.get("id") != PROMPT_ID or event.get("command") != "prompt":
            return
        if event.get("success") is not True:
            raise _error("pi_rpc_rejected", "pi rejected the prompt command")
        self.acknowledged = True

    def _message_start(self, event) -> None:
        message = event.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            self._message_index += 1

    def _message_update(self, event) -> str | None:
        update = event.get("assistantMessageEvent")
        if not isinstance(update, dict):
            raise _invalid_jsonl()
        kind = update.get("type")
        if kind == "text_delta":
            return _required_text(update, "delta")
        if kind in {"thinking_start", "thinking_delta", "thinking_end"}:
            self._thinking_update(kind, update)
        if kind == "error":
            raise _error("pi_model_error", "pi model request failed")
        return None

    def _thinking_update(self, kind, update) -> None:
        index = _required_index(update.get("contentIndex"))
        key = self._message_index, index
        if kind == "thinking_start":
            self._thinking[key] = ""
        elif kind == "thinking_delta":
            self._thinking[key] = self._thinking.get(key, "") + _required_text(update, "delta")
        else:
            self._thinking[key] = _required_text(update, "content")
        self.items.append(_thinking_item(kind, key, self._thinking[key]))

    def _message_end(self, event) -> None:
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            return
        _add_usage(self.usage, message.get("usage"))

    def _tool(self, event) -> None:
        tool_id = event.get("toolCallId")
        name = event.get("toolName")
        if not isinstance(tool_id, str) or not isinstance(name, str):
            raise _invalid_jsonl()
        phase = event["type"].removeprefix("tool_execution_")
        item = {"id": tool_id, "type": "tool_execution", "name": name}
        if phase == "start":
            item["arguments"] = event.get("args")
        elif phase == "update":
            item["partial_result"] = event.get("partialResult")
        if phase == "end":
            item["result"] = event.get("result")
            item["is_error"] = event.get("isError") is True
        self.items.append({"phase": _phase(phase), "item": item})

    def _agent_end(self, event) -> None:
        if event.get("willRetry") is True:
            return
        if not self.acknowledged:
            raise _error("pi_rpc_missing_ack", "pi ended before acknowledging the prompt")
        message = _last_assistant(event.get("messages"))
        _require_successful_message(message)
        self.text = _message_text(message)
        if not any(self.usage.values()):
            _add_usage(self.usage, message.get("usage"))
        self.terminal = True

    def _extension_ui(self, event) -> None:
        if event.get("method") in {"select", "confirm", "input", "editor"}:
            raise _error("pi_extension_ui_unsupported", "pi requested interactive extension input")

    def result(self) -> ModelResult:
        return ModelResult(
            {"role": "assistant", "content": self.text},
            self.usage, self.items,
        )


async def _collect(process, prompt: str, emit: Emit, timeout: float) -> ModelResult:
    parser = PiEventParser()
    _start_stderr(process)
    await _send(process, {"id": PROMPT_ID, "type": "prompt", "message": prompt})
    try:
        result = await asyncio.wait_for(_read_turn(process, parser, emit), timeout)
    except TimeoutError as error:
        failure = _error("pi_timeout", f"pi timed out after {timeout:g}s")
        _attach_items(failure, parser)
        raise failure from error
    except TraceError as error:
        _attach_items(error, parser)
        raise
    await _close_completed_process(process)
    return result


async def _read_turn(process, parser, emit) -> ModelResult:
    while not parser.terminal:
        line = await process.stdout.readline()
        if not line:
            raise _premature_exit(process)
        delta = parser.consume(_decode_event(line))
        if delta:
            await emit(delta)
    return parser.result()


async def _send(process, command: dict[str, Any]) -> None:
    writer = getattr(process, "stdin", None)
    if writer is None or writer.is_closing():
        raise _error("pi_rpc_closed", "pi RPC input is closed")
    writer.write((json.dumps(command, separators=(",", ":")) + "\n").encode())
    await writer.drain()


async def _send_abort(process) -> None:
    if process.returncode is not None:
        return
    try:
        await _send(process, {"id": "abort-1", "type": "abort"})
        await asyncio.sleep(0)
    except (BrokenPipeError, ConnectionResetError, TraceError):
        return


async def _close_completed_process(process) -> None:
    _close_stdin(process)
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
    except TimeoutError:
        await _bounded_stop(process)
    await _finish_stderr(process)


async def _bounded_stop(process) -> None:
    if process.returncode is not None:
        return
    _signal_process(process, signal.SIGTERM, "terminate")
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
        return
    except TimeoutError:
        _signal_process(process, signal.SIGKILL, "kill")
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
    except TimeoutError as error:
        raise _error("pi_termination_timeout", "pi did not terminate") from error


def _signal_process(process, value, fallback) -> None:
    if os.name == "posix" and getattr(process, "pid", None):
        try:
            os.killpg(process.pid, value)
        except ProcessLookupError:
            return
    else:
        getattr(process, fallback)()


def _start_stderr(process) -> None:
    if getattr(process, "stderr", None) is not None:
        process.pi_stderr_task = asyncio.create_task(_discard(process.stderr))


async def _discard(stream) -> None:
    while await stream.read(4096):
        pass


async def _finish_stderr(process) -> None:
    task = getattr(process, "pi_stderr_task", None)
    if task is None:
        return
    try:
        await asyncio.wait_for(task, TERMINATE_TIMEOUT)
    except TimeoutError:
        task.cancel()


def _close_stdin(process) -> None:
    writer = getattr(process, "stdin", None)
    if writer is not None and not writer.is_closing():
        writer.close()


def _decode_event(line: bytes) -> dict[str, Any]:
    try:
        value = json.loads(line.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _invalid_jsonl() from error
    if not isinstance(value, dict):
        raise _invalid_jsonl()
    return value


def _event_type(event: dict[str, Any]) -> str:
    value = event.get("type")
    if not isinstance(value, str) or not value:
        raise _invalid_jsonl()
    return value


def _premature_exit(process) -> TraceError:
    if process.returncode:
        return _error("pi_cli_failed", f"pi exited with status {process.returncode}")
    return _error("pi_incomplete_stream", "pi exited before agent_end")


def _invalid_jsonl() -> TraceError:
    return _error("pi_invalid_jsonl", "pi returned invalid JSONL")


def _error(code: str, message: str) -> TraceError:
    return TraceError(code, message)


def _attach_items(error: TraceError, parser: PiEventParser) -> None:
    error.provider_items = list(parser.items)


def _required_text(value: dict, field: str) -> str:
    text = value.get(field)
    if not isinstance(text, str):
        raise _invalid_jsonl()
    return text


def _required_index(value) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise _invalid_jsonl()
    return value


def _thinking_item(kind, key, text) -> dict[str, Any]:
    phases = {"thinking_start": "started", "thinking_delta": "updated"}
    item = {"id": f"thinking-{key[0]}-{key[1]}", "type": "reasoning", "text": text}
    return {"phase": phases.get(kind, "completed"), "item": item}


def _phase(value: str) -> str:
    phase = {"start": "started", "update": "updated", "end": "completed"}.get(value)
    if phase is None:
        raise _invalid_jsonl()
    return phase


def _last_assistant(messages) -> dict[str, Any]:
    if not isinstance(messages, list):
        raise _invalid_jsonl()
    value = next(
        (item for item in reversed(messages)
         if isinstance(item, dict) and item.get("role") == "assistant"),
        None,
    )
    if value is None:
        raise _invalid_jsonl()
    return value


def _require_successful_message(message: dict[str, Any]) -> None:
    reason = message.get("stopReason")
    if reason == "aborted":
        raise _error("pi_aborted", "pi model request was aborted")
    if reason == "error":
        raise _error("pi_model_error", "pi model request failed")
    if reason not in {"stop", "length", "toolUse", "deferred"}:
        raise _invalid_jsonl()


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        raise _invalid_jsonl()
    return "".join(
        item.get("text", "") for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )


def _add_usage(total: dict[str, int], usage) -> None:
    if not isinstance(usage, dict):
        raise _invalid_jsonl()
    for target, source in USAGE_FIELDS.items():
        value = usage.get(source, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise _invalid_jsonl()
        total[target] += value


def _empty_usage() -> dict[str, int]:
    return {key: 0 for key in USAGE_FIELDS}


def _latest_user(messages: list[dict]) -> str:
    return next(
        (item.get("content", "") for item in reversed(messages)
         if item.get("role") == "user"),
        "",
    )


def _system_option(messages: list[dict], context: dict[str, Any]) -> list[str]:
    value = next(
        (item.get("content", "") for item in messages if item.get("role") == "system"),
        context.get("system_prompt", ""),
    )
    return ["--append-system-prompt", value] if value else []


def _model_option(model: str) -> list[str]:
    return [] if model == "default" else ["--model", model]


def _named_option(context: dict[str, Any]) -> list[str]:
    value = context.get("session_name")
    return ["--name", value] if value else []


def _runtime_options(context: dict[str, Any]) -> list[str]:
    values = ["--thinking", context["reasoning_effort"]]
    if context.get("sandbox") == "read-only":
        values.extend(["--tools", "read,grep,find,ls"])
    return values


def _environment() -> dict[str, str]:
    home = os.environ.get("HOME") or str(Path.home())
    agent_dir = os.environ.get("PI_CODING_AGENT_DIR") or str(Path(home) / ".pi" / "agent")
    return {
        "HOME": home, "PI_CODING_AGENT_DIR": agent_dir, "PI_OFFLINE": "1",
        "PI_TELEMETRY": "0", "LANG": "C.UTF-8", "PATH": CHILD_PATH,
    }


def _version_probe(executable: str):
    return subprocess.run(
        [executable, "--version"], env={"LANG": "C.UTF-8", "PATH": CHILD_PATH},
        capture_output=True, text=True, check=False, timeout=PROBE_TIMEOUT,
    )


def _session_id(process, continuations) -> str | None:
    value = getattr(process, "runtime_session_id", None)
    return value or next((item for item in continuations if item), None)


def _executable_identity(path: str | None) -> str | None:
    try:
        content = Path(path).read_bytes() if path else None
    except OSError:
        return None
    return hashlib.sha256(content).hexdigest() if content is not None else None


def _checked_at() -> str:
    return datetime.now(UTC).isoformat()


def _reason(code: str, probe: str) -> dict[str, str]:
    return {"code": code, "probe": probe}


def _process_group_options() -> dict[str, int | bool]:
    if os.name == "posix":
        return {"start_new_session": True}
    return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}

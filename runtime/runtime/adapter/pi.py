from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import AdapterResult, TurnRequest

PI_VERSION = "0.84.3"
PROMPT_ID = "prompt-1"
ABORT_TIMEOUT = 0.1
TERMINATE_TIMEOUT = 2.0
LOCALE_KEYS = (
    "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "LC_COLLATE", "LC_MONETARY",
    "LC_NUMERIC", "LC_TIME", "LC_MESSAGES", "LC_PAPER", "LC_NAME",
    "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT", "LC_IDENTIFICATION",
)
REASONING_PHASES = {
    "thinking_start": "started",
    "thinking_delta": "updated",
    "thinking_end": "completed",
}
MESSAGE_UPDATE_TYPES = {
    "text_start",
    "text_end",
    "toolcall_start",
    "toolcall_delta",
    "toolcall_end",
}
TOOL_PHASES = {
    "tool_execution_start": "started",
    "tool_execution_update": "updated",
    "tool_execution_end": "completed",
}
IGNORED_EVENTS = {
    "agent_start", "turn_start", "turn_end", "message_start", "message_end",
    "queue_update", "compaction_start", "compaction_end", "auto_retry_start",
    "summarization_retry_scheduled", "summarization_retry_attempt_start",
    "summarization_retry_finished", "model_select", "thinking_level_select",
    "input", "user_bash", "bash_execution_update", "tool_call", "tool_result",
    "context", "before_agent_start", "before_provider_request",
    "before_provider_headers", "after_provider_response", "resources_discover",
    "project_trust", "session_before_compact", "session_before_fork",
    "session_before_switch", "session_before_tree", "session_compact",
    "session_info_changed", "session_shutdown", "session_start", "session_tree",
}


class PiAdapterError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class PiHandle:
    process: Any
    stderr_task: asyncio.Task
    cancelled: bool = False


class PiAdapter:
    adapter_id = "pi"
    supports_multiple_writers = False

    def __init__(self, executable: str, version: str, timeout: float = 300.0):
        self.executable = executable
        self.version = version
        self.timeout = timeout

    @classmethod
    def detect(cls, executable: str = "pi", timeout: float = 300.0) -> PiAdapter:
        resolved = shutil.which(executable)
        if resolved is None:
            raise PiAdapterError("pi_not_found", "pi executable not found on PATH")
        path = os.path.realpath(resolved)
        version = _probe_version(path)
        return cls(path, version, timeout)

    async def start(self, request: TurnRequest) -> PiHandle:
        command = self._command(request)
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=_workspace(request),
                env=_environment(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **_process_group_options(),
            )
        except (OSError, ValueError) as error:
            raise PiAdapterError("pi_process", "failed to start pi") from error
        return PiHandle(process, asyncio.create_task(_drain(process.stderr)))

    def _command(self, request: TurnRequest) -> list[str]:
        snapshot = request.agent_snapshot
        model = _setting(snapshot, "model", "default")
        instructions = _setting(snapshot, "instructions", "")
        thinking = snapshot.get("thinking")
        if thinking is not None:
            thinking = _setting(snapshot, "thinking", "")
        command = [self.executable, "--mode", "rpc", "--no-session"]
        if model != "default":
            command.extend(("--model", model))
        if instructions:
            command.extend(("--append-system-prompt", instructions))
        if thinking:
            command.extend(("--thinking", thinking))
        return command

    async def submit(self, handle, request, emit) -> AdapterResult:
        try:
            return await _submit(handle, request, emit, self.timeout)
        except PiAdapterError:
            if handle.cancelled:
                return AdapterResult(status="cancelled")
            await _cleanup(handle)
            raise

    async def cancel(self, handle: PiHandle, request: TurnRequest) -> None:
        handle.cancelled = True
        await _cleanup(handle)


class PiEventParser:
    def __init__(self):
        self.acknowledged = False
        self.agent_ended = False
        self.agent_error: PiAdapterError | None = None
        self.finished = False
        self.result_text = ""

    def consume(self, line: bytes) -> list[dict[str, Any]]:
        event = _decode(line)
        kind = _event_type(event)
        if kind == "response":
            self._response(event)
        elif kind == "message_update":
            return _text_delta(event)
        elif kind in TOOL_PHASES:
            return [_tool_event(kind, event)]
        elif kind == "agent_end":
            self._agent_end(event)
        elif kind == "agent_settled":
            self._settled()
        else:
            self._auxiliary(kind, event)
        return []

    def _response(self, event: dict[str, Any]) -> None:
        if event.get("id") != PROMPT_ID or event.get("command") != "prompt":
            return
        if event.get("success") is not True:
            raise PiAdapterError("pi_protocol", "pi rejected the prompt command")
        self.acknowledged = True

    def _agent_end(self, event: dict[str, Any]) -> None:
        if not self.acknowledged:
            raise PiAdapterError("pi_protocol", "pi ended before prompt acknowledgement")
        if event.get("willRetry") is True:
            return
        message = _last_assistant(event.get("messages"))
        try:
            _validate_stop_reason(message)
        except PiAdapterError as error:
            if error.code != "pi_process":
                raise
            self.agent_error = error
            self.agent_ended = False
            return
        self.result_text = _message_text(message)
        self.agent_error = None
        self.agent_ended = True

    def _settled(self) -> None:
        if self.agent_error is not None:
            raise self.agent_error
        if not self.agent_ended:
            raise PiAdapterError("pi_protocol", "pi settled before agent_end")
        self.finished = True

    def _auxiliary(self, kind: str, event: dict[str, Any]) -> None:
        if kind == "extension_error" or kind == "session_compact_failed":
            raise PiAdapterError("pi_process", f"pi reported {kind}")
        if kind == "auto_retry_end" and event.get("success") is False:
            raise PiAdapterError("pi_process", "pi automatic retry failed")
        if kind == "extension_ui_request":
            if event.get("method") in {"select", "confirm", "input", "editor"}:
                raise PiAdapterError("pi_protocol", _interactive_detail(kind, event))
            return
        if kind in {"ui_prompt_start", "ui_prompt_end"}:
            raise PiAdapterError("pi_protocol", _interactive_detail(kind, event))
        if kind not in IGNORED_EVENTS:
            raise PiAdapterError("pi_protocol", f"unsupported pi event: {kind}")


def _interactive_detail(kind: str, event: dict[str, Any]) -> str:
    method = event.get("method")
    suffix = f": {method}" if isinstance(method, str) and method else ""
    return f"pi requested unsupported interactive input{suffix} ({kind})"


async def _submit(handle, request, emit, timeout: float) -> AdapterResult:
    if not isinstance(request.input, str):
        raise PiAdapterError("pi_input", "pi prompt must be a string")
    parser = PiEventParser()
    await _send(handle.process, {"id": PROMPT_ID, "type": "prompt", "message": request.input})
    try:
        await asyncio.wait_for(_read(handle.process, parser, emit), timeout)
    except asyncio.TimeoutError as error:
        raise PiAdapterError("pi_process", f"pi timed out after {timeout:g}s") from error
    await _close_completed(handle)
    return AdapterResult(result_text=parser.result_text)


async def _read(process, parser, emit) -> None:
    while not parser.finished:
        line = await process.stdout.readline()
        if not line:
            await process.wait()
            raise _exit_error(process, parser.agent_ended or parser.agent_error is not None)
        for event in parser.consume(line):
            await emit(event)


async def _send(process, command: dict[str, Any]) -> None:
    writer = process.stdin
    if writer is None or writer.is_closing():
        raise PiAdapterError("pi_protocol", "pi RPC input is closed")
    try:
        writer.write((json.dumps(command, separators=(",", ":")) + "\n").encode())
        await writer.drain()
    except (BrokenPipeError, ConnectionResetError) as error:
        raise PiAdapterError("pi_process", "pi RPC input failed") from error


async def _send_abort(process) -> None:
    if process.returncode is not None:
        return
    try:
        await _send(process, {"type": "abort"})
        await asyncio.sleep(0)
    except PiAdapterError:
        return


async def _close_completed(handle: PiHandle) -> None:
    _close_stdin(handle.process)
    try:
        await asyncio.wait_for(handle.process.wait(), TERMINATE_TIMEOUT)
    except asyncio.TimeoutError:
        await _stop(handle.process)
    await _finish_stderr(handle.stderr_task)


async def _cleanup(handle: PiHandle) -> None:
    await _send_abort(handle.process)
    try:
        await asyncio.wait_for(handle.process.wait(), ABORT_TIMEOUT)
    except asyncio.TimeoutError:
        _close_stdin(handle.process)
        await _stop(handle.process)
    await _finish_stderr(handle.stderr_task)


async def _stop(process) -> None:
    if process.returncode is not None:
        return
    _signal(process, signal.SIGTERM, "terminate")
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
        return
    except asyncio.TimeoutError:
        _signal(process, signal.SIGKILL, "kill")
    try:
        await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
    except asyncio.TimeoutError as error:
        raise PiAdapterError("pi_process", "pi did not terminate") from error


def _signal(process, value, fallback) -> None:
    if os.name == "posix" and getattr(process, "pid", None):
        try:
            os.killpg(process.pid, value)
        except ProcessLookupError:
            return
    else:
        getattr(process, fallback)()


async def _drain(stream) -> None:
    while await stream.read(4096):
        pass


async def _finish_stderr(task: asyncio.Task) -> None:
    try:
        await asyncio.wait_for(task, TERMINATE_TIMEOUT)
    except asyncio.TimeoutError:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def _close_stdin(process) -> None:
    writer = process.stdin
    if writer is not None and not writer.is_closing():
        writer.close()


def _decode(line: bytes) -> dict[str, Any]:
    try:
        value = json.loads(line.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PiAdapterError("pi_protocol", "pi returned invalid JSONL") from error
    if not isinstance(value, dict):
        raise PiAdapterError("pi_protocol", "pi returned a non-object JSONL event")
    return value


def _event_type(event: dict[str, Any]) -> str:
    value = event.get("type")
    if not isinstance(value, str) or not value:
        raise PiAdapterError("pi_protocol", "pi event has no type")
    return value


def _text_delta(event: dict[str, Any]) -> list[dict[str, Any]]:
    update = event.get("assistantMessageEvent")
    if not isinstance(update, dict):
        raise PiAdapterError("pi_protocol", "pi message update is invalid")
    if update.get("type") != "text_delta":
        kind = update.get("type")
        if kind in REASONING_PHASES:
            return [_reasoning_event(kind, update)]
        if kind == "error":
            raise PiAdapterError("pi_process", "pi model request failed")
        if kind in MESSAGE_UPDATE_TYPES:
            return []
        raise PiAdapterError("pi_protocol", "pi message update type is invalid")
    value = update.get("delta")
    if not isinstance(value, str):
        raise PiAdapterError("pi_protocol", "pi text delta is invalid")
    return [{"type": "delta", "data": {"text": value}}]


def _reasoning_event(kind: str, update: dict[str, Any]) -> dict[str, Any]:
    index = update.get("contentIndex")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise PiAdapterError("pi_protocol", "pi reasoning content index is invalid")
    field = "delta" if kind == "thinking_delta" else "content"
    value = update.get(field, "")
    if not isinstance(value, str):
        raise PiAdapterError("pi_protocol", "pi reasoning text is invalid")
    return {
        "type": "reasoning",
        "data": {"phase": REASONING_PHASES[kind], "content_index": index, "text": value},
    }


def _tool_event(kind: str, event: dict[str, Any]) -> dict[str, Any]:
    tool_id, name = event.get("toolCallId"), event.get("toolName")
    if not isinstance(tool_id, str) or not isinstance(name, str):
        raise PiAdapterError("pi_protocol", "pi tool event is invalid")
    data = {"phase": TOOL_PHASES[kind], "id": tool_id, "name": name}
    if kind == "tool_execution_start":
        data["arguments"] = event.get("args")
    elif kind == "tool_execution_update":
        data["partial_result"] = event.get("partialResult")
    else:
        if not isinstance(event.get("isError"), bool):
            raise PiAdapterError("pi_protocol", "pi tool result error flag is invalid")
        data.update(result=event.get("result"), is_error=event["isError"])
    return {"type": "tool", "data": data}


def _last_assistant(messages) -> dict[str, Any]:
    if not isinstance(messages, list):
        raise PiAdapterError("pi_protocol", "pi agent_end messages are invalid")
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "assistant":
            return message
    raise PiAdapterError("pi_protocol", "pi agent_end has no assistant message")


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        raise PiAdapterError("pi_protocol", "pi assistant content is invalid")
    return "".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )


def _validate_stop_reason(message: dict[str, Any]) -> None:
    reason = message.get("stopReason")
    if reason == "error":
        raise PiAdapterError("pi_process", "pi model request failed")
    if reason == "aborted":
        raise PiAdapterError("pi_process", "pi model request aborted")
    if reason not in {"stop", "length", "toolUse", "deferred"}:
        raise PiAdapterError("pi_protocol", "pi assistant stop reason is invalid")


def _probe_version(path: str) -> str:
    try:
        result = subprocess.run(
            [path, "--version"],
            env=_environment(),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PiAdapterError("pi_configuration", "pi version probe failed") from error
    version = result.stdout.strip()
    if result.returncode != 0 or version != PI_VERSION:
        raise PiAdapterError("pi_configuration", f"unsupported pi version: {version or 'unknown'}")
    return version


def _workspace(request: TurnRequest) -> str:
    value = request.agent_snapshot.get("workspace", str(Path.cwd()))
    if not isinstance(value, str) or not value or not Path(value).is_dir():
        raise PiAdapterError("pi_configuration", "pi workspace is not a directory")
    return value


def _setting(snapshot: dict[str, Any], name: str, default: str) -> str:
    value = snapshot.get(name, default)
    if not isinstance(value, str) or (name != "instructions" and not value):
        raise PiAdapterError("pi_configuration", f"pi setting is invalid: {name}")
    return value


def _environment() -> dict[str, str]:
    home = os.environ.get("HOME") or str(Path.home())
    agent_dir = os.environ.get("PI_CODING_AGENT_DIR") or str(Path(home) / ".pi" / "agent")
    environment = {key: os.environ[key] for key in LOCALE_KEYS if key in os.environ}
    environment.update(
        {
            "HOME": home,
            "PI_CODING_AGENT_DIR": agent_dir,
            "PI_TELEMETRY": "0",
            "PATH": os.environ.get("PATH", os.defpath),
        }
    )
    return environment


def _exit_error(process, agent_ended: bool = False) -> PiAdapterError:
    if process.returncode not in (None, 0):
        return PiAdapterError("pi_process", f"pi exited with status {process.returncode}")
    expected = "agent_settled" if agent_ended else "agent_end"
    return PiAdapterError("pi_protocol", f"pi exited before {expected}")


def _process_group_options() -> dict[str, int | bool]:
    if os.name == "posix":
        return {"start_new_session": True}
    return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}

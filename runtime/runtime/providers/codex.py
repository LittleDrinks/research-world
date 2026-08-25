from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from typing import Any

from .base import Emit, ModelResult
from ..types import TraceError

VERSION = re.compile(r"codex-cli\s+(\S+)")


class CodexProvider:
    id = "codex"

    def __init__(self, executable: str = "codex", timeout: float = 300.0):
        resolved = shutil.which(executable)
        if not resolved:
            raise RuntimeError("codex executable not found")
        self.executable = resolved
        self.timeout = timeout
        self.version: str | None = None
        self._processes: dict[str, Any] = {}
        self._cancelled: set[str] = set()

    @classmethod
    def detected(cls) -> CodexProvider | None:
        executable = shutil.which("codex")
        version = _version(executable) if executable else None
        if version is None:
            return None
        provider = cls(executable)
        provider.version = version
        return provider

    async def generate(
        self, model, messages, tools, emit: Emit, context
    ) -> ModelResult:
        session_id = context["runtime_session_id"]
        process = await self._start(model, context)
        self._processes[session_id] = process
        if session_id in self._cancelled:
            process.terminate()
        try:
            return await _collect(process, _latest_user(messages), emit, self.timeout)
        finally:
            self._processes.pop(session_id, None)
            self._cancelled.discard(session_id)

    async def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Codex CLI does not expose embeddings")

    def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
        process = self._processes.get(session_id)
        if process and process.returncode is None:
            process.terminate()

    async def _start(self, model, context):
        return await asyncio.create_subprocess_exec(
            *self._command(model, context),
            cwd=context["workspace"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        effort = context.get("reasoning_effort", "medium")
        options = [
            "--json", "--skip-git-repo-check", "-m", model,
            "-c", f'model_reasoning_effort="{effort}"',
        ]
        session_id = context.get("provider_session_id")
        if session_id:
            return [self.executable, "exec", "resume", *options, session_id, "-"]
        return [self.executable, "exec", *options, "-s", context["sandbox"], "-"]


def _version(executable: str | None) -> str | None:
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, "--version"], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = VERSION.search(result.stdout) if result.returncode == 0 else None
    return match.group(1) if match else None


async def _collect(process, prompt: str, emit: Emit, timeout: float) -> ModelResult:
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(prompt.encode()), timeout
        )
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise TraceError("cli_timeout", f"codex timed out after {timeout:g}s") from error
    if process.returncode:
        raise TraceError("cli_failed", f"codex exited {process.returncode}")
    events = _events(stdout)
    text = _agent_text(events)
    if text:
        await emit(text)
    return ModelResult({"role": "assistant", "content": text}, _usage(events), _thread_id(events))


def _events(stdout: bytes) -> list[dict]:
    try:
        values = [
            json.loads(line) for line in stdout.decode().splitlines() if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TraceError("cli_invalid_jsonl", "codex returned invalid JSONL") from error
    if not all(_valid_event(item) for item in values):
        raise TraceError("cli_invalid_jsonl", "codex returned invalid JSONL")
    _terminal(values)
    return values


def _terminal(events: list[dict]) -> None:
    terminal = next(
        (item["type"] for item in reversed(events) if item["type"].startswith("turn.")),
        None,
    )
    if terminal == "turn.completed":
        return
    if terminal in {"turn.failed", "turn.cancelled"}:
        raise TraceError("cli_stream_failed", "codex returned a failed terminal stream")
    raise TraceError("cli_incomplete_stream", "codex returned an incomplete terminal stream")


def _valid_event(event: object) -> bool:
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        return False
    if "item" in event and not isinstance(event["item"], dict):
        return False
    if "usage" in event and not isinstance(event["usage"], dict):
        return False
    return all(
        isinstance(event["usage"].get(key, 0), int)
        for key in ("input_tokens", "output_tokens")
    ) if "usage" in event else True


def _latest_user(messages: list[dict]) -> str:
    system = next(
        (item["content"] for item in messages if item["role"] == "system"), ""
    )
    user = next(
        (item["content"] for item in reversed(messages) if item["role"] == "user"), ""
    )
    return f"{system}\n\n{user}" if len(messages) <= 2 else user


def _agent_text(events: list[dict]) -> str:
    values = [
        item.get("item", {}).get("text", "")
        for item in events
        if item.get("item", {}).get("type") == "agent_message"
    ]
    return "\n".join(value for value in values if value)


def _thread_id(events: list[dict]) -> str | None:
    event = next((item for item in events if item.get("type") == "thread.started"), {})
    return event.get("thread_id")


def _usage(events: list[dict]) -> dict[str, int]:
    event = next(
        (item for item in reversed(events) if item.get("type") == "turn.completed"), {}
    )
    usage = event.get("usage") or {}
    return {
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
    }

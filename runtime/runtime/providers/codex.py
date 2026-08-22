from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any

from .base import Emit, ModelResult


class CodexProvider:
    id = "codex"

    def __init__(self, executable: str = "codex"):
        resolved = shutil.which(executable)
        if not resolved:
            raise RuntimeError("codex executable not found")
        self.executable = resolved

    @classmethod
    def detected(cls) -> CodexProvider | None:
        return cls() if shutil.which("codex") else None

    async def generate(
        self, model, messages, tools, emit: Emit, context
    ) -> ModelResult:
        command = self._command(model, context)
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=context["workspace"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return await _collect(process, _latest_user(messages), emit)

    async def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Codex CLI does not expose embeddings")

    def _command(self, model: str, context: dict[str, Any]) -> list[str]:
        common = [self.executable, "-a", "never", "exec"]
        session_id = context.get("provider_session_id")
        options = ["--json", "--skip-git-repo-check", "-m", model]
        if session_id:
            return [*common, "resume", *options, session_id, "-"]
        sandbox = context.get("sandbox", "read-only")
        return [*common, *options, "-s", sandbox, "-"]


async def _collect(process, prompt: str, emit: Emit) -> ModelResult:
    stdout, stderr = await process.communicate(prompt.encode())
    if process.returncode:
        raise RuntimeError(
            f"codex exited {process.returncode}: {stderr.decode()[-500:]}"
        )
    events = [json.loads(line) for line in stdout.decode().splitlines() if line.strip()]
    text = _agent_text(events)
    if text:
        await emit(text)
    return ModelResult(
        {"role": "assistant", "content": text}, _usage(events), _thread_id(events)
    )


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

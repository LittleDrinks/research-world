import asyncio

import pytest
from runtime.providers.codex import CodexProvider, _collect
from runtime.service import _provider_context


def test_codex_command_uses_agent_reasoning_and_sandbox():
    provider = CodexProvider("echo")
    context = {
        "workspace": "/tmp",
        "sandbox": "workspace-write",
        "reasoning_effort": "high",
    }

    command = provider._command("gpt-test", context)

    assert 'model_reasoning_effort="high"' in command
    assert command[command.index("-s") + 1] == "workspace-write"


def test_provider_context_reads_agent_options():
    meta = {
        "workspace": "/tmp",
        "agent_spec": {
            "options": {"reasoning_effort": "low", "sandbox": "read-only"}
        },
    }

    context = _provider_context(meta, [])

    assert context["reasoning_effort"] == "low"
    assert context["sandbox"] == "read-only"


class HangingProcess:
    def __init__(self):
        self.killed = False

    async def communicate(self, _prompt):
        await asyncio.Event().wait()

    def kill(self):
        self.killed = True

    async def wait(self):
        return 1


async def test_codex_timeout_kills_process():
    process = HangingProcess()

    with pytest.raises(RuntimeError, match="timed out after"):
        await _collect(process, "prompt", lambda _text: None, 0.001)

    assert process.killed

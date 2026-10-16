import pytest
from runtime.service import Runtime
from runtime.runtimes import REALM, RuntimeAdapter, RuntimeDescriptor
from runtime.types import SessionSpecInvalid, ToolPlanDrift
from tests.helpers import FakeProvider, endpoint

V1 = [{"name": "tool__lab__echo", "description": "", "parameters": {"type": "object"}}]
V2 = [
    {
        "name": "tool__lab__echo",
        "description": "",
        "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
    }
]


def spec():
    return {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "openai-compatible", "realm": "container:runtime"},
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use tools.",
        "tools": ["lab"],
    }


class DriftAdapter:
    def __init__(self):
        self.operations = V1

    def inspect(self):
        return {
            "id": "lab",
            "name": "Lab",
            "description": "",
            "source": "test",
            "status": "ready",
        }

    async def open(self):
        return DriftBound(self.operations)


class DriftBound:
    def __init__(self, operations):
        self.tool_id = "lab"
        self.specs = [
            {"type": "function", "function": dict(item)} for item in operations
        ]

    async def close(self):
        return None


def patch_adapters(monkeypatch, adapter):
    monkeypatch.setattr(
        "runtime.service.discover_adapters",
        lambda workspace, extra=(): {"lab": adapter},
    )


def generic_runtime(path, endpoints):
    adapter = RuntimeAdapter(RuntimeDescriptor("openai-compatible", REALM), ("openai-compatible",))
    return Runtime(path / "data", endpoints, [adapter])


async def test_prompt_fails_when_tool_operations_drift(tmp_path, monkeypatch):
    adapter = DriftAdapter()
    patch_adapters(monkeypatch, adapter)
    provider = FakeProvider([{"role": "assistant", "content": "done"}])
    runtime = generic_runtime(tmp_path, [endpoint(provider)])
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    adapter.operations = V2
    with pytest.raises(ToolPlanDrift, match="start a new session"):
        await runtime.prompt(launched["session_id"], [{"type": "text", "text": "go"}])

    trace = runtime.inspect(launched["session_id"])
    assert trace["status"] == "error"
    assert not provider.requests


def test_tool_plan_drift_uses_session_restart_recovery():
    assert issubclass(ToolPlanDrift, SessionSpecInvalid)


class FailingAdapter:
    def inspect(self):
        return {
            "id": "lab",
            "name": "Lab",
            "description": "",
            "source": "test",
            "status": "ready",
        }

    async def open(self):
        raise RuntimeError("tool failed to open: lab")


async def test_failed_tool_handshake_creates_no_session(tmp_path, monkeypatch):
    patch_adapters(monkeypatch, FailingAdapter())
    runtime = generic_runtime(tmp_path, [endpoint(FakeProvider([]))])

    with pytest.raises(RuntimeError, match="tool failed to open"):
        await runtime.launch({"workspace": str(tmp_path), "agent_spec": spec()})

    assert runtime.trace.sessions() == []

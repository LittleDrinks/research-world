import json
import sys
from types import SimpleNamespace

import pytest
from runtime.adapters import BoundMcp, parse_definition
from runtime.service import Runtime
from tests.helpers import FakeProvider, endpoint

SERVER = """
from mcp.server.fastmcp import FastMCP

server = FastMCP("test")

@server.tool()
def echo(text: str) -> str:
    return f"mcp:{text}"

server.run()
"""


async def test_selected_tool_exposes_and_executes_operations(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    call = {
        "id": "m1",
        "type": "function",
        "function": {"name": "tool__proof_mcp__echo", "arguments": '{"text":"hello"}'},
    }
    provider = FakeProvider(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            {"role": "assistant", "content": "done"},
        ]
    )
    definition = parse_definition(
        {
            "id": "proof_mcp",
            "name": "Proof MCP",
            "description": "Formal proof tools",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(script)],
        },
        "runtime",
    )
    runtime = Runtime(
        tmp_path / "data", [endpoint(provider)], tool_definitions=[definition]
    )
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use tools.",
        "tools": ["proof_mcp"],
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})
    artifacts = ArtifactClient()

    await runtime.prompt(
        launched["session_id"], [{"type": "text", "text": "echo"}], artifacts
    )

    assert "tool__proof_mcp__echo" in str(provider.requests[0]["tools"])
    assert "mcp:hello" in str(provider.requests[1]["messages"])
    assert "artifact:" + "a" * 64 in str(provider.requests[1]["messages"])
    method, capture = artifacts.calls[0]
    assert method == "research/capture_artifact"
    assert set(capture) == {"content", "media_type", "tool"}
    assert capture["media_type"] == "application/json"
    assert capture["tool"] == "tool__proof_mcp__echo"
    assert "mcp:hello" in str(json.loads(capture["content"]))


class ArtifactClient:
    def __init__(self):
        self.calls = []

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        return {"id": "artifact:" + "a" * 64}


async def test_tool_dying_after_launch_closes_the_failed_turn(tmp_path, monkeypatch):
    adapter = FlakyAdapter()
    monkeypatch.setattr(
        "runtime.service.discover_adapters",
        lambda workspace, extra=(): {"offline": adapter},
    )
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use tools.",
        "tools": ["offline"],
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})

    adapter.alive = False
    with pytest.raises(RuntimeError, match="tool failed to open"):
        await runtime.prompt(launched["session_id"], [{"type": "text", "text": "go"}])

    trace = runtime.inspect(launched["session_id"])
    assert trace["status"] == "error"
    assert [event["type"] for event in trace["events"]][-2:] == ["error", "turn_end"]


class FlakyAdapter:
    def __init__(self):
        self.alive = True

    def inspect(self):
        return {
            "id": "offline",
            "name": "Offline",
            "description": "",
            "source": "test",
            "status": "ready",
        }

    async def open(self):
        if not self.alive:
            raise RuntimeError("tool failed to open: offline")
        return FlakyBound()


class FlakyBound:
    tool_id = "offline"
    specs = [
        {
            "type": "function",
            "function": {
                "name": "tool__offline__ping",
                "description": "",
                "parameters": {"type": "object"},
            },
        }
    ]

    async def close(self):
        return None


async def test_tool_plan_snapshot_carries_no_location_or_command(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    definition = parse_definition(
        {
            "id": "proof_mcp",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(script)],
        },
        "runtime",
    )
    runtime = Runtime(
        tmp_path / "data",
        [endpoint(FakeProvider([]))],
        tool_definitions=[definition],
    )
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use tools.",
        "tools": ["proof_mcp"],
    }

    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})

    meta = runtime.inspect(launched["session_id"])["session"]
    [entry] = meta["tool_plan"]
    assert entry["id"] == "proof_mcp"
    assert [op["name"] for op in entry["operations"]] == ["tool__proof_mcp__echo"]
    frozen = json.dumps(meta)
    assert str(script) not in frozen
    assert sys.executable not in frozen


class PagedSession:
    def __init__(self):
        self.cursors = []

    async def list_tools(self, cursor=None):
        self.cursors.append(cursor)
        tools = [_tool("one")] if cursor is None else [_tool("two")]
        return SimpleNamespace(tools=tools, nextCursor=None if cursor else "p2")


def _tool(name):
    return SimpleNamespace(
        name=name,
        model_dump=lambda **_: {"description": "", "inputSchema": {"type": "object"}},
    )


def _bound():
    definition = parse_definition(
        {"id": "lab", "transport": "stdio", "command": "lab-mcp"}, "test"
    )
    return BoundMcp(definition)


async def test_mcp_operations_follow_list_tools_pagination():
    bound = _bound()
    session = PagedSession()

    await bound._load_operations(session)

    assert [s["function"]["name"] for s in bound.specs] == [
        "tool__lab__one",
        "tool__lab__two",
    ]
    assert session.cursors == [None, "p2"]


class BadSession:
    def __init__(self, name):
        self.name = name

    async def list_tools(self, cursor=None):
        return SimpleNamespace(tools=[_tool(self.name)], nextCursor=None)


@pytest.mark.parametrize("name", ["has space", "x" * 80])
async def test_rejects_operation_names_breaking_model_function_encoding(name):
    with pytest.raises(ValueError, match="invalid tool operation name"):
        await _bound()._load_operations(BadSession(name))


async def test_tool_config_and_credentials_do_not_enter_trace(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    monkeypatch.setenv("LAB_DB_TOKEN", "top-secret")
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    definition = parse_definition(
        {
            "id": "lab-db",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(script)],
            "env": {"API_KEY": "${LAB_DB_TOKEN}"},
        },
        "runtime",
    )
    runtime = Runtime(
        tmp_path / "data",
        [endpoint(FakeProvider([]))],
        tool_definitions=[definition],
    )
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use evidence.",
        "tools": ["lab-db"],
    }

    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})

    trace = json.dumps(runtime.inspect(launched["session_id"])["session"])
    assert "top-secret" not in trace
    assert "LAB_DB_TOKEN" not in trace
    assert str(script) not in trace

import json
import sys

import pytest

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


async def test_selected_mcp_server_exposes_and_executes_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    call = {
        "id": "m1",
        "type": "function",
        "function": {"name": "mcp__lean4__echo", "arguments": '{"text":"hello"}'},
    }
    provider = FakeProvider(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            {"role": "assistant", "content": "done"},
        ]
    )
    runtime = Runtime(tmp_path / "data", [endpoint(provider)])
    runtime.register_connector(
        {
            "id": "lean4",
            "name": "Lean 4",
            "description": "Formal proof tools",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(script)],
        }
    )
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use MCP.",
        "connectors": ["lean4"],
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})
    artifacts = ArtifactClient()

    await runtime.prompt(
        launched["session_id"], [{"type": "text", "text": "echo"}], artifacts
    )

    assert "mcp__lean4__echo" in str(provider.requests[0]["tools"])
    assert "mcp:hello" in str(provider.requests[1]["messages"])
    assert "artifact:" + "a" * 64 in str(provider.requests[1]["messages"])
    method, capture = artifacts.calls[0]
    assert method == "research/capture_artifact"
    assert set(capture) == {"content", "media_type", "connector_tool"}
    assert capture["media_type"] == "application/json"
    assert capture["connector_tool"] == "mcp__lean4__echo"
    assert "mcp:hello" in str(json.loads(capture["content"]))


class ArtifactClient:
    def __init__(self):
        self.calls = []

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        return {"id": "artifact:" + "a" * 64}


async def test_unreachable_remote_connector_closes_the_failed_turn(tmp_path):
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    runtime.register_connector(
        {"id": "offline", "transport": "http", "url": "http://127.0.0.1:1/mcp"}
    )
    agent = {
        "id": "researcher",
        "name": "Researcher",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Use MCP.",
        "connectors": ["offline"],
    }
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": agent})

    with pytest.raises(RuntimeError, match="connector session failed"):
        await runtime.prompt(launched["session_id"], [{"type": "text", "text": "go"}])

    trace = runtime.inspect(launched["session_id"])
    assert trace["status"] == "error"
    assert [event["type"] for event in trace["events"]][-2:] == ["error", "turn_end"]

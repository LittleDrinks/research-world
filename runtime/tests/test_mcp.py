import sys

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

    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "echo"}])

    assert "mcp__lean4__echo" in str(provider.requests[0]["tools"])
    assert "mcp:hello" in str(provider.requests[1]["messages"])

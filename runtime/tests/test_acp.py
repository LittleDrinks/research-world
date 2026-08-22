import json

from acp import (
    PROTOCOL_VERSION,
    ReadTextFileResponse,
    connect_to_agent,
    text_block,
)
from acp._transport import memory_transport_pair
from acp.agent import AgentSideConnection
from acp.schema import ClientCapabilities, Implementation

from runtime.acp_agent import RuntimeAgent
from runtime.service import Runtime
from tests.helpers import FakeProvider


class ProjectClient:
    def __init__(self):
        self.updates = []

    async def session_update(self, session_id, update, **kwargs):
        self.updates.append(update)

    async def read_text_file(self, session_id, path, **kwargs):
        assert path == "@D-008"
        return ReadTextFileResponse(content="node evidence")


async def test_acp_is_the_runtime_transport(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_API_BASE", "https://api.test/v1")
    monkeypatch.setenv("RUNTIME_API_KEY", "secret")
    monkeypatch.setenv("RUNTIME_MODEL", "qwen-test")
    call = {
        "id": "r1",
        "type": "function",
        "function": {
            "name": "read_resource",
            "arguments": json.dumps({"node_id": "D-008"}),
        },
    }
    provider = FakeProvider(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            {"role": "assistant", "content": "verified"},
        ]
    )
    runtime = Runtime(tmp_path / "data", {"openai-compatible": provider})
    left, right = memory_transport_pair()
    agent = AgentSideConnection(lambda client: RuntimeAgent(runtime), left)
    project = ProjectClient()
    connection = connect_to_agent(project, right)
    try:
        await connection.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=ClientCapabilities(),
            client_info=Implementation(name="test", title="Test", version="1"),
        )
        launched = await connection.ext_method(
            "runtime/launch",
            {
                "workspace": str(tmp_path),
                "agent_spec": {
                    "id": "researcher",
                    "name": "Researcher",
                    "runtime": "openai-compatible",
                    "model": "qwen-test",
                    "instructions": "Use cited nodes.",
                    "tools": ["read_resource"],
                },
            },
        )
        await connection.prompt(launched["session_id"], [text_block("Check @D-008")])
        inspected = await connection.ext_method(
            "runtime/inspect", {"session_id": launched["session_id"]}
        )
    finally:
        await connection.close()
        await agent.close()

    assert inspected["messages"][-1]["content"] == "verified"
    assert project.updates

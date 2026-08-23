import json
import sys

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
from runtime.tools import ToolBox
from tests.helpers import FakeProvider, endpoint


class ProjectClient:
    def __init__(self):
        self.updates = []

    async def session_update(self, session_id, update, **kwargs):
        self.updates.append(update)

    async def read_text_file(self, session_id, path, **kwargs):
        assert path == "@D-008"
        return ReadTextFileResponse(content="node evidence")

    async def ext_method(self, method, params):
        assert method == "research/graph_query"
        return {"id": params["node_id"], "life_state": "admitted"}


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
    runtime = Runtime(tmp_path / "data", [endpoint(provider)])
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
                    "endpoint": "openai-compatible",
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


async def test_graph_query_crosses_the_client_boundary(tmp_path):
    client = ProjectClient()
    async with ToolBox(tmp_path, {}, ("graph_query",), [], client) as tools:
        content, failed = await tools.call(
            "session", "graph_query", '{"action":"get","node_id":"D-008"}'
        )
    assert failed is False
    assert json.loads(content) == {"id": "D-008", "life_state": "admitted"}


async def test_runtime_extensions_register_connector_and_embed(tmp_path):
    runtime = Runtime(
        tmp_path / "data",
        [endpoint(FakeProvider([]), "embedding", ("embed-model",))],
    )
    agent = RuntimeAgent(runtime)

    connector = await agent.ext_method(
        "runtime/connectors/register",
        {
            "connector": {
                "id": "lean4",
                "name": "Lean 4",
                "transport": "stdio",
                "command": sys.executable,
            }
        },
    )
    vectors = await agent.ext_method(
        "runtime/embed",
        {"endpoint": "embedding", "model": "embed-model", "texts": ["proof"]},
    )

    assert connector["id"] == "lean4"
    assert vectors == {"value": [[0.0]]}

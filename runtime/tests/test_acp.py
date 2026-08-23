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


async def test_report_validate_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    facts = [{"text": "Result", "claim_id": "claim:1", "source_ids": ["S-1"]}]
    async with ToolBox(tmp_path, {}, ("report_validate",), [], client) as tools:
        content, failed = await tools.call(
            "session",
            "report_validate",
            json.dumps({"facts": facts, "endpoint_ready": True}),
        )

    assert failed is False
    assert json.loads(content) == {"valid": True, "delivery_level": 4}
    assert client.calls == [
        ("research/report_validate", {"facts": facts, "endpoint_ready": True})
    ]


async def test_submit_observation_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    value = observation()
    async with ToolBox(tmp_path, {}, ("submit_observation",), [], client) as tools:
        content, failed = await tools.call(
            "session", "submit_observation", json.dumps(value)
        )

    assert failed is False
    assert json.loads(content)["life_state"] == "pending"
    assert client.calls == [("research/submit_observation", value)]


def test_kernel_tools_are_exposed_only_when_selected(tmp_path):
    selected = ToolBox(
        tmp_path, {}, ("report_validate", "submit_observation"), [], None
    )
    omitted = ToolBox(tmp_path, {}, (), [], None)

    assert "report_validate" in tool_names(selected)
    assert "submit_observation" in tool_names(selected)
    assert "report_validate" not in tool_names(omitted)
    assert "submit_observation" not in tool_names(omitted)


async def test_connector_call_without_kernel_client_fails_explicitly(tmp_path):
    tools = ToolBox(tmp_path, {}, (), [], None)
    tools.mcp = ConnectorResult()

    content, failed = await tools.call("session", "mcp__db__query", "{}")

    assert failed is True
    assert "client does not provide artifact capture" in content


async def test_runtime_extensions_register_connector_and_embed(tmp_path):
    runtime = Runtime(
        tmp_path / "data",
        [
            endpoint(
                FakeProvider([]),
                "embedding",
                (),
                embedding_models=("embed-model",),
            )
        ],
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


class KernelClient:
    def __init__(self):
        self.calls = []

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        if method == "research/report_validate":
            return {"valid": True, "delivery_level": 4}
        if method == "research/submit_observation":
            return {"id": "node:observation", "life_state": "pending"}
        raise AssertionError(method)


class ConnectorResult:
    def __init__(self):
        self.names = {"mcp__db__query": ("db", "query")}
        self.specs = []

    async def call(self, name, values):
        return '[{"type":"text","text":"result"}]', False


def tool_names(tools):
    return {value["function"]["name"] for value in tools.specs()}


def observation():
    return {
        "kind": "source",
        "payload": {"title": "Run 7"},
        "provenance": {"actor": "researcher:li", "method": "four-probe"},
        "observed_at": "2026-08-23T09:30:00+08:00",
        "artifact_ids": ["artifact:" + "a" * 64],
        "parent_id": "node:direction",
    }

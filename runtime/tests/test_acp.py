import json

import pytest
from acp import (
    PROTOCOL_VERSION,
    ReadTextFileResponse,
    RequestError,
    connect_to_agent,
    text_block,
)
from acp._transport import memory_transport_pair
from acp.agent import AgentSideConnection
from acp.schema import ClientCapabilities, Implementation
from runtime.acp_agent import RuntimeAgent
from runtime.endpoints import Endpoint
from runtime.runtimes import CodexRuntimeAdapter
from runtime.service import Runtime
from runtime.tools import ToolBox
from runtime.types import CapabilityNotFound
from tests.helpers import FakeProvider, endpoint
from tests.test_codex import ready_provider


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


class PublicationClient:
    def __init__(self):
        self.calls = []
        self.updates = []

    async def session_update(self, session_id, update, **kwargs):
        self.updates.append(update)

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        return {"status": "failed", "assessment": {"gaps": []}}


async def test_acp_is_the_runtime_transport(tmp_path, monkeypatch):
    project, agent, connection = _acp_connection(_resource_runtime(tmp_path, monkeypatch))
    try:
        inspected = await _resource_session(connection, tmp_path)
    finally:
        await connection.close()
        await agent.close()

    assert inspected["messages"][-1]["content"] == "verified"
    assert project.updates


async def test_acp_default_codex_uses_declared_credentialless_endpoint(tmp_path, monkeypatch):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "auth.json").write_text('{"token":"test"}')
    monkeypatch.setenv("CODEX_HOME", str(home))
    endpoint = Endpoint("chat", "Chat", "openai-compatible", ("gpt",), (), 1, None)
    runtime = Runtime(tmp_path / "data", [endpoint], [CodexRuntimeAdapter(ready_provider())])

    response = await RuntimeAgent(runtime).new_session(str(tmp_path))

    assert runtime.state.read(response.session_id)["agent_spec"]["endpoint"] == "chat"


async def test_acp_default_uses_codex_when_generic_endpoint_is_credentialless(tmp_path, monkeypatch):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "auth.json").write_text('{"token":"test"}')
    monkeypatch.setenv("CODEX_HOME", str(home))
    monkeypatch.setattr("runtime.runtimes.CodexProvider.detected", lambda: ready_provider())
    chat = Endpoint("chat", "Chat", "openai-compatible", ("gpt",), (), 1, None)
    runtime = Runtime(tmp_path / "data", [chat])

    response = await RuntimeAgent(runtime).new_session(str(tmp_path))

    spec = runtime.state.read(response.session_id)["agent_spec"]
    assert spec["runtime"]["id"] == "codex"
    assert (spec["endpoint"], spec["model"]) == ("chat", "gpt")


async def test_acp_default_fails_when_catalog_has_no_eligible_pair(tmp_path, monkeypatch):
    monkeypatch.setattr("runtime.runtimes.CodexProvider.detected", lambda: ready_provider())
    foreign = Endpoint("foreign", "Foreign", "foreign", ("gpt",), (), 1, None, available=True)
    runtime = Runtime(tmp_path / "data", [foreign])

    with pytest.raises(CapabilityNotFound, match="no model endpoint"):
        await RuntimeAgent(runtime).new_session(str(tmp_path))


def _resource_runtime(path, monkeypatch):
    for key, value in {"RUNTIME_API_BASE": "https://api.test/v1", "RUNTIME_API_KEY": "secret", "RUNTIME_MODEL": "qwen-test"}.items():
        monkeypatch.setenv(key, value)
    return Runtime(path / "data", [endpoint(FakeProvider(_resource_responses()))])


async def _resource_session(connection, workspace):
    await _initialize(connection)
    launched = await connection.ext_method("runtime/launch", _resource_launch(workspace))
    await connection.prompt(launched["session_id"], [text_block("Check @D-008")])
    return await connection.ext_method("runtime/inspect", {"session_id": launched["session_id"]})


def _resource_responses():
    call = {"id": "r1", "type": "function", "function": {"name": "read_resource", "arguments": json.dumps({"node_id": "D-008"})}}
    return [{"role": "assistant", "content": "", "tool_calls": [call]}, {"role": "assistant", "content": "verified"}]


def _acp_connection(runtime):
    left, right = memory_transport_pair()
    agent = AgentSideConnection(lambda client: RuntimeAgent(runtime), left)
    project = ProjectClient()
    return project, agent, connect_to_agent(project, right)


async def _initialize(connection):
    await connection.initialize(protocol_version=PROTOCOL_VERSION, client_capabilities=ClientCapabilities(), client_info=Implementation(name="test", title="Test", version="1"))


def _resource_launch(workspace):
    spec = {"id": "researcher", "name": "Researcher", "runtime": {"id": "openai-compatible", "realm": "container:runtime"}, "endpoint": "openai-compatible", "model": "qwen-test", "instructions": "Use cited nodes.", "tools": ["read_resource"]}
    return {"workspace": str(workspace), "agent_spec": spec}


async def test_graph_query_crosses_the_client_boundary(tmp_path):
    client = ProjectClient()
    async with ToolBox(tmp_path, {}, ("graph_query",), {}, client) as tools:
        content, failed = await tools.call(
            "session", "graph_query", '{"action":"get","node_id":"D-008"}'
        )
    assert failed is False
    assert json.loads(content) == {"id": "D-008", "life_state": "admitted"}


async def test_export_bibtex_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    artifact_id = "artifact:" + "a" * 64
    async with ToolBox(tmp_path, {}, ("export_bibtex",), {}, client) as tools:
        content, failed = await tools.call(
            "session", "export_bibtex", json.dumps({"artifact_id": artifact_id})
        )

    assert failed is False
    assert json.loads(content) == {"id": artifact_id, "content": "@article{x}"}
    assert client.calls == [("research/export_bibtex", {"artifact_id": artifact_id})]


async def test_report_projection_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    async with ToolBox(tmp_path, {}, ("report_projection",), {}, client) as tools:
        content, failed = await tools.call("session", "report_projection", "{}")

    assert failed is False
    assert json.loads(content) == {"facts": [], "claims": [], "sources": []}
    assert client.calls == [("research/report_projection", {})]


async def test_publish_report_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    values = {"title": "Orbit"}
    async with ToolBox(tmp_path, {}, ("publish_report",), {}, client) as tools:
        content, failed = await tools.call("session", "publish_report", json.dumps(values))

    assert failed is False
    assert json.loads(content)["status"] == "failed"
    assert client.calls == [("research/publish_report", {**values, "_session_id": "session"})]


@pytest.mark.parametrize(
    ("arguments", "status"), [({"title": "Orbit"}, "failed"), ({}, "failed")],
)
async def test_publish_report_emits_safe_acp_lifecycle(tmp_path, arguments, status):
    call = _publish_call(arguments)
    provider = FakeProvider(
        [{"role": "assistant", "content": "", "tool_calls": [call]},
         {"role": "assistant", "content": "done"}]
    )
    client = PublicationClient()
    runtime = Runtime(tmp_path / "data", [endpoint(provider)])
    launched = await runtime.launch({"workspace": str(tmp_path), "agent_spec": _report_agent()})
    await runtime.prompt(launched["session_id"], [{"type": "text", "text": "publish"}], client)
    first, last = client.updates
    assert _lifecycle(client.updates) == [
        ("tool_call", "in_progress"), ("tool_call_update", status)
    ]
    assert first.tool_call_id == last.tool_call_id
    assert first.tool_call_id.startswith("report:")
    assert (first.title, first.kind) == ("发布科研报告", "other")
    assert all(update.content is update.raw_input is update.raw_output is None for update in client.updates)


def _publish_call(arguments):
    return {
        "id": "report-call",
        "type": "function",
        "function": {"name": "publish_report", "arguments": json.dumps(arguments)},
    }


def _report_agent():
    return {
        "id": "reporter",
        "name": "Reporter",
        "endpoint": "openai-compatible",
        "model": "qwen-test",
        "instructions": "Publish the report.",
        "tools": ["publish_report"],
    }


def _lifecycle(updates):
    return [(item.session_update, item.status) for item in updates]


async def test_submit_observation_crosses_the_client_boundary(tmp_path):
    client = KernelClient()
    value = observation()
    async with ToolBox(tmp_path, {}, ("submit_observation",), {}, client) as tools:
        content, failed = await tools.call(
            "session", "submit_observation", json.dumps(value)
        )

    assert failed is False
    assert json.loads(content)["life_state"] == "pending"
    assert client.calls == [("research/submit_observation", value)]


async def test_kernel_tools_are_exposed_only_when_selected(tmp_path):
    async with ToolBox(
        tmp_path, {}, ("report_projection", "publish_report", "submit_observation"), {}, None
    ) as selected:
        selected_names = tool_names(selected)
    async with ToolBox(tmp_path, {}, (), {}, None) as omitted:
        omitted_names = tool_names(omitted)

    assert "report_projection" in selected_names
    assert "publish_report" in selected_names
    assert "submit_observation" in selected_names
    assert "report_projection" not in omitted_names
    assert "submit_observation" not in omitted_names


async def test_external_call_without_kernel_client_fails_explicitly(tmp_path):
    async with ToolBox(tmp_path, {}, ("db",), {"db": FakeAdapter()}, None) as tools:
        content, failed = await tools.call("session", "tool__db__query", "{}")

    assert failed is True
    assert "client does not provide artifact capture" in content


async def test_runtime_extension_embed(tmp_path):
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

    vectors = await agent.ext_method(
        "runtime/embed",
        {"endpoint": "embedding", "model": "embed-model", "texts": ["proof"]},
    )

    assert vectors == {"value": [[0.0]]}


async def test_runtime_extension_validates_agent_spec(tmp_path):
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    agent = RuntimeAgent(runtime)

    result = await agent.ext_method(
        "runtime/agents/validate", {"agent_spec": valid_agent_spec()}
    )

    assert result == {"valid": True}


@pytest.mark.parametrize(
    ("method", "params"),
    [("runtime/agents/validate", {"agent_spec": {"id": "bad"}})],
)
async def test_runtime_user_input_errors_cross_acp_as_invalid_params(
    tmp_path, method, params
):
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    left, right = memory_transport_pair()
    agent = AgentSideConnection(lambda client: RuntimeAgent(runtime), left)
    connection = connect_to_agent(ProjectClient(), right)
    try:
        with pytest.raises(RequestError) as raised:
            await connection.ext_method(method, params)
    finally:
        await connection.close()
        await agent.close()

    assert raised.value.code == -32602
    assert raised.value.data["details"]


async def test_prompt_on_legacy_session_meta_surfaces_validation_error(tmp_path):
    runtime = Runtime(tmp_path / "data", [endpoint(FakeProvider([]))])
    _legacy_trace(runtime, tmp_path)
    left, right = memory_transport_pair()
    agent = AgentSideConnection(lambda client: RuntimeAgent(runtime), left)
    connection = connect_to_agent(ProjectClient(), right)
    try:
        with pytest.raises(RequestError) as raised:
            await connection.prompt("s-legacy", [text_block("hi")])
    finally:
        await connection.close()
        await agent.close()

    assert raised.value.code == -32602
    assert raised.value.data["code"] == "session_spec_invalid"
    assert "Additional properties are not allowed" in raised.value.data["details"]


def _legacy_trace(runtime, workspace):
    spec = {"id": "researcher", "name": "Researcher", "runtime": {"id": "openai-compatible", "realm": "container:runtime"}, "model": "qwen-test", "instructions": "Use cited nodes.", "mcp_servers": []}
    runtime.trace.create("s-legacy", {"agent_spec": spec, "workspace": str(workspace), "parent": None, "mode": "resume", "skills": []})


class KernelClient:
    def __init__(self):
        self.calls = []

    async def ext_method(self, method, params):
        self.calls.append((method, params))
        if method == "research/report_projection":
            return {"facts": [], "claims": [], "sources": []}
        if method == "research/publish_report":
            return {"status": "failed", "assessment": {"gaps": []}}
        if method == "research/export_bibtex":
            return {"id": params["artifact_id"], "content": "@article{x}"}
        if method == "research/submit_observation":
            return {"id": "node:observation", "life_state": "pending"}
        raise AssertionError(method)


class FakeAdapter:
    def inspect(self):
        return {"id": "db", "name": "DB", "description": "", "source": "test", "status": "ready"}

    async def open(self):
        return FakeBound()


class FakeBound:
    def __init__(self):
        self.specs = [
            {"type": "function", "function": {"name": "tool__db__query", "parameters": {}}}
        ]

    async def invoke(self, operation, values, session_id=""):
        return '[{"type":"text","text":"result"}]', False

    async def close(self):
        return None


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


def valid_agent_spec():
    return {
        "id": "researcher",
        "name": "Researcher",
        "runtime": {"id": "openai-compatible", "realm": "container:runtime"},
        "endpoint": "embedding",
        "model": "embed-model",
        "instructions": "Use evidence.",
    }


async def test_toolbox_rolls_back_opened_tools_in_reverse_order(tmp_path):
    events = []
    adapters = {
        "a": TrackAdapter("a", events),
        "b": TrackAdapter("b", events),
        "c": FailingAdapter("c", events),
        "d": TrackAdapter("d", events),
    }

    with pytest.raises(RuntimeError, match="open failed: c"):
        async with ToolBox(tmp_path, {}, ("a", "b", "c", "d"), adapters, None):
            pass

    assert events == ["open:a", "open:b", "open:c", "close:b", "close:a"]


class TrackAdapter:
    def __init__(self, tool_id, events):
        self.tool_id = tool_id
        self.events = events

    async def open(self):
        self.events.append(f"open:{self.tool_id}")
        return TrackBound(self.tool_id, self.events)


class TrackBound:
    def __init__(self, tool_id, events):
        self.tool_id = tool_id
        self.events = events
        self.specs = []

    async def close(self):
        self.events.append(f"close:{self.tool_id}")


class FailingAdapter:
    def __init__(self, tool_id, events):
        self.tool_id = tool_id
        self.events = events

    async def open(self):
        self.events.append(f"open:{self.tool_id}")
        raise RuntimeError(f"open failed: {self.tool_id}")

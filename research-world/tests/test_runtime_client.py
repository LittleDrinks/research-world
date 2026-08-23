from __future__ import annotations

import json
from contextlib import asynccontextmanager

import pytest
from acp import RequestError

from server.kernel import KernelCommand, ResearchKernel
from server.runtime_client import (
    KernelClient,
    RuntimeCapabilityError,
    RuntimeClient,
    RuntimeEmbedding,
    RuntimeRequestError,
    _prompt_blocks,
    _websocket_url,
    json_object,
)


class RetryingRuntime(RuntimeClient):
    def __init__(self, outputs):
        self.outputs = outputs
        self.prompts = []
        self.launch_values = []
        self.project_id = "project:test"

    async def launch(self, agent_spec, workspace, **values):
        self.launch_values.append(values)
        return "session:test"

    async def prompt(self, session_id, message, project_id=None):
        self.prompts.append(message)

    async def inspect(self, session_id):
        if not self.prompts:
            return {"session": {"id": session_id}, "turns": []}
        output = self.outputs[len(self.prompts) - 1]
        turn = {"id": f"turn:{len(self.prompts)}", "output": output, "events": []}
        return {"session": {"id": session_id}, "turns": [turn]}

    async def _workspace(self):
        return "/workspace"


class FailingExtensionRuntime(RuntimeClient):
    def __init__(self, error):
        super().__init__("http://runtime:8098", "project:test")
        self.error = error
        self.kernel = object()

    @asynccontextmanager
    async def _connect(self, _client):
        yield FailingConnection(self.error)


class FailingConnection:
    def __init__(self, error):
        self.error = error

    async def ext_method(self, _method, _params):
        raise self.error

    async def prompt(self, _session_id, _blocks):
        raise self.error


def test_runtime_url_uses_acp_websocket():
    assert _websocket_url("http://runtime:8098") == "ws://runtime:8098/acp/"
    assert _websocket_url("https://runtime.test/base") == "wss://runtime.test/base/acp/"


def test_runtime_client_requires_kernel_binding():
    runtime = RuntimeClient("http://runtime:8098")

    with pytest.raises(RuntimeError, match="bound ResearchKernel"):
        runtime._kernel()


@pytest.mark.asyncio
async def test_invalid_runtime_extension_params_become_value_error():
    error = RequestError.invalid_params({"details": "agent name is required"})
    runtime = FailingExtensionRuntime(error)

    with pytest.raises(ValueError, match="agent name is required"):
        await runtime.validate_agent({"id": "bad"})


@pytest.mark.asyncio
async def test_internal_runtime_extension_error_becomes_capability_error():
    error = RequestError.internal_error({"details": "runtime unavailable"})
    runtime = FailingExtensionRuntime(error)

    with pytest.raises(RuntimeCapabilityError, match="runtime unavailable"):
        await runtime.validate_agent({"id": "bad"})


@pytest.mark.asyncio
async def test_prompt_stream_surfaces_runtime_error_details():
    error = RequestError.invalid_params(
        {
            "code": "session_spec_invalid",
            "details": "Additional properties are not allowed ('mcp_servers')",
        }
    )
    runtime = FailingExtensionRuntime(error)

    with pytest.raises(RuntimeRequestError, match="Additional properties") as raised:
        async for _ in runtime.prompt_stream("session:test", "hi"):
            pass

    assert raised.value.code == "session_spec_invalid"


def test_json_object_repairs_fenced_model_output():
    assert json_object('```json\n{"answer": 42}\n```') == {"answer": 42}


@pytest.mark.asyncio
async def test_json_retries_missing_required_field_in_same_session():
    runtime = RetryingRuntime(['{"left":"x"}', '{"duplicate":false}'])
    result = await runtime._json({}, "compare", {}, ("duplicate",))
    assert result["duplicate"] is False
    assert result["_session_id"] == "session:test"
    assert "缺少必需字段：duplicate" in runtime.prompts[1]


@pytest.mark.asyncio
async def test_json_retries_malformed_output_in_same_session():
    runtime = RetryingRuntime(["not json", '{"duplicate":true}'])
    result = await runtime._json({}, "compare", {}, ("duplicate",))
    assert result["duplicate"] is True
    assert "valid JSON object" in runtime.prompts[1]


@pytest.mark.asyncio
async def test_json_retries_non_object_output_in_same_session():
    runtime = RetryingRuntime(
        ['{"subject":"direction"}\n{"duplicate":false}', '{"duplicate":false}']
    )
    result = await runtime._json({}, "compare", {}, ("duplicate",))
    assert result["duplicate"] is False
    assert "valid JSON object" in runtime.prompts[1]


@pytest.mark.asyncio
async def test_json_reuses_completed_operation_without_prompting():
    runtime = RetryingRuntime(['{"duplicate":false}'])
    runtime.prompts.append("already completed")

    result = await runtime._json({}, "compare", {}, ("duplicate",), "run:1:review")

    assert result["duplicate"] is False
    assert runtime.prompts == ["already completed"]
    assert runtime.launch_values[0]["session_id"].startswith("s-op-")


def test_prompt_resources_are_node_ids():
    blocks = _prompt_blocks("比较证据", ["node:a", "node:b"])
    values = [block.model_dump(by_alias=True, exclude_none=True) for block in blocks]
    assert values[0] == {"type": "text", "text": "比较证据"}
    assert [item["uri"] for item in values[1:]] == ["node:a", "node:b"]


@pytest.mark.asyncio
async def test_kernel_client_exposes_project_nodes(world, project, tmp_path):
    node = world.nodes(project["id"])[0]
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = KernelClient(kernel, project["id"])
    bare_id = node["id"].removeprefix("node:")
    content = await client.read_text_file("session", f"@{bare_id}")
    assert json.loads(content.content)["id"] == node["id"]
    result = await client.ext_method(
        "research/graph_query", {"action": "get", "node_id": bare_id}
    )
    assert result["id"] == node["id"]


@pytest.mark.asyncio
async def test_kernel_client_captures_artifact_then_submits_observation(
    world, project, tmp_path
):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    client = KernelClient(kernel, project["id"])
    artifact = await client.ext_method(
        "research/capture_artifact",
        {"content": "measured result", "media_type": "text/plain"},
    )
    assert set(artifact) == {"id", "sha256", "media_type", "size", "created_at"}
    observation = await client.ext_method(
        "research/submit_observation", observation_record(artifact["id"])
    )
    await kernel.command(
        KernelCommand(
            "resolve_admission",
            project["id"],
            {"node_id": observation["id"], "decision": "approve"},
        )
    )
    projection = await client.ext_method("research/report_projection", {})

    assert observation["life_state"] == "pending"
    assert observation["payload"]["artifact_ids"] == [artifact["id"]]
    assert projection["artifacts"] == [artifact]


def test_embedding_wraps_runtime_failure():
    class FailedRuntime:
        async def embed(self, endpoint, model, texts):
            raise RuntimeError("embeddings unavailable")

    with pytest.raises(RuntimeCapabilityError, match="embeddings unavailable"):
        RuntimeEmbedding(FailedRuntime(), "primary", "embedding-model")("orbit")


def observation_record(artifact_id):
    return {
        "kind": "source",
        "payload": {"title": "Tool measurement"},
        "provenance": {"actor": "tool:test", "method": "tool call"},
        "observed_at": "2026-08-23T09:30:00+08:00",
        "artifact_ids": [artifact_id],
    }

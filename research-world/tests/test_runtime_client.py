from __future__ import annotations

import json

import pytest

from server.runtime_client import (
    KernelClient,
    RuntimeCapabilityError,
    RuntimeClient,
    RuntimeEmbedding,
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

    def _workspace(self):
        return "/workspace"


def test_runtime_url_uses_acp_websocket():
    assert _websocket_url("http://runtime:8098") == "ws://runtime:8098/acp/"
    assert _websocket_url("https://runtime.test/base") == "wss://runtime.test/base/acp/"


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
async def test_kernel_client_exposes_project_nodes(world, project):
    node = world.nodes(project["id"])[0]
    client = KernelClient(world, project["id"])
    bare_id = node["id"].removeprefix("node:")
    content = await client.read_text_file("session", f"@{bare_id}")
    assert json.loads(content.content)["id"] == node["id"]
    result = await client.ext_method(
        "research/graph_query", {"action": "get", "node_id": bare_id}
    )
    assert result["id"] == node["id"]


def test_embedding_wraps_runtime_failure():
    class FailedRuntime:
        async def embed(self, model, texts):
            raise RuntimeError("embeddings unavailable")

    with pytest.raises(RuntimeCapabilityError, match="embeddings unavailable"):
        RuntimeEmbedding(FailedRuntime(), "embedding-model")("orbit")

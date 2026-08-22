from __future__ import annotations

import json

import pytest

from server.runtime_client import (
    KernelClient,
    RuntimeCapabilityError,
    RuntimeEmbedding,
    _prompt_blocks,
    _websocket_url,
    json_object,
)


def test_runtime_url_uses_acp_websocket():
    assert _websocket_url("http://runtime:8098") == "ws://runtime:8098/acp"
    assert _websocket_url("https://runtime.test/base") == "wss://runtime.test/base/acp"


def test_json_object_repairs_fenced_model_output():
    assert json_object('```json\n{"answer": 42}\n```') == {"answer": 42}


def test_prompt_resources_are_node_ids():
    blocks = _prompt_blocks("比较证据", ["node:a", "node:b"])
    values = [block.model_dump(by_alias=True, exclude_none=True) for block in blocks]
    assert values[0] == {"type": "text", "text": "比较证据"}
    assert [item["uri"] for item in values[1:]] == ["node:a", "node:b"]


@pytest.mark.asyncio
async def test_kernel_client_exposes_project_nodes(world, project):
    node = world.nodes(project["id"])[0]
    client = KernelClient(world, project["id"])
    content = await client.read_text_file("session", f"@{node['id']}")
    assert json.loads(content.content)["id"] == node["id"]
    result = await client.ext_method(
        "research/graph_query", {"action": "get", "node_id": node["id"]}
    )
    assert result["id"] == node["id"]


def test_embedding_wraps_runtime_failure():
    class FailedRuntime:
        async def embed(self, model, texts):
            raise RuntimeError("embeddings unavailable")

    with pytest.raises(RuntimeCapabilityError, match="embeddings unavailable"):
        RuntimeEmbedding(FailedRuntime(), "embedding-model")("orbit")

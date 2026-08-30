import asyncio

import pytest

from runtime.runtime import AdapterResult, Runtime


class RecordingKernel:
    def __init__(self):
        self.calls = []

    def record(self, project_id, record_type, content, artifact_ids=()):
        self.calls.append(("record", project_id, record_type, content, artifact_ids))
        return {"id": "record-1", "project_id": project_id}

    def connect(self, project_id, source_id, target_id, relation_type):
        self.calls.append(
            ("connect", project_id, source_id, target_id, relation_type)
        )
        return {"id": "relation-1", "project_id": project_id}

    def remove_record(self, project_id, record_id):
        self.calls.append(("remove_record", project_id, record_id))

    def remove_relation(self, project_id, relation_id):
        self.calls.append(("remove_relation", project_id, relation_id))

    def local_map(self, project_id, query):
        self.calls.append(("local_map", project_id, query))
        return {"project_id": project_id, "query": query}


class ToolAdapter:
    adapter_id = "tool"
    supports_multiple_writers = True

    async def start(self, request):
        return request

    async def submit(self, handle, request, emit):
        handle.value = request.tools.invoke(
            "kernel",
            "record",
            {
                "project_id": "project-1",
                "record_type": "direction",
                "content": {"text": "candidate"},
            },
        )
        return AdapterResult(result_text="recorded")

    async def cancel(self, handle, request):
        return None


class KernelOperationsAdapter(ToolAdapter):
    async def submit(self, handle, request, emit):
        tools = request.tools
        tools.invoke(
            "kernel",
            "record",
            {"project_id": "project-1", "record_type": "source", "content": {}},
        )
        tools.invoke(
            "kernel",
            "connect",
            {
                "project_id": "project-2",
                "source_id": "source-1",
                "target_id": "direction-1",
                "relation_type": "supports",
            },
        )
        tools.invoke(
            "kernel",
            "remove_record",
            {"project_id": "project-1", "record_id": "record-1"},
        )
        tools.invoke(
            "kernel",
            "remove_relation",
            {"project_id": "project-2", "relation_id": "relation-1"},
        )
        tools.invoke(
            "kernel",
            "local_map",
            {"project_id": "project-1", "query": {"text": "orbit", "limit": 5}},
        )
        return AdapterResult(result_text="kernel operations complete")


class MMRAdapter(ToolAdapter):
    def __init__(self):
        self.selection = None

    async def submit(self, handle, request, emit):
        self.selection = request.tools.invoke(
            "brainstorm",
            "mmr",
            {
                "candidates": [
                    {"id": "b", "relevance": 0.9},
                    {"id": "a", "relevance": 0.9},
                    {"id": "c", "relevance": 0.8},
                ],
                "similarities": {
                    "a": {"b": 1.0, "c": 0.0},
                    "b": {"a": 1.0, "c": 0.0},
                    "c": {"a": 0.0, "b": 0.0},
                },
                "count": 2,
                "diversity_weight": 0.5,
            },
        )
        return AdapterResult(result_text="mmr complete")


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


@pytest.mark.asyncio
async def test_adapter_can_use_kernel_tool_record_operation(tmp_path):
    kernel = RecordingKernel()
    adapter = ToolAdapter()
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch({"adapter": "tool", "tools": ["kernel"]})
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "record"})

    await _events(runtime, turn["id"])

    assert kernel.calls == [
        ("record", "project-1", "direction", {"text": "candidate"}, ())
    ]


@pytest.mark.asyncio
async def test_kernel_tool_forwards_project_scoped_operations(tmp_path):
    kernel = RecordingKernel()
    adapter = KernelOperationsAdapter()
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch({"adapter": "tool", "tools": ["kernel"]})
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "tools"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {
        "status": "completed",
        "result_text": "kernel operations complete",
    }
    assert kernel.calls == [
        ("record", "project-1", "source", {}, ()),
        ("connect", "project-2", "source-1", "direction-1", "supports"),
        ("remove_record", "project-1", "record-1"),
        ("remove_relation", "project-2", "relation-1"),
        ("local_map", "project-1", {"text": "orbit", "limit": 5}),
    ]


@pytest.mark.asyncio
async def test_brainstorm_mmr_is_deterministic_and_does_not_touch_kernel(tmp_path):
    kernel = RecordingKernel()
    adapter = MMRAdapter()
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch({"adapter": "tool", "tools": ["brainstorm"]})
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "select"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {"status": "completed", "result_text": "mmr complete"}
    assert adapter.selection == [
        {"id": "a", "relevance": 0.9},
        {"id": "c", "relevance": 0.8},
    ]
    assert kernel.calls == []

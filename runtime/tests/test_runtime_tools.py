import asyncio
import subprocess
import sys
from pathlib import Path

import pytest
from kernel_contract import LocalMapQuery

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


def test_runtime_tools_loads_without_the_server_source_path():
    result = subprocess.run(
        [sys.executable, "-c", "from runtime.runtime_tools import RuntimeTools"],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


_KERNEL_OPERATIONS = (
    ("record", {"project_id": "project-1", "record_type": "source", "content": {}}),
    (
        "connect",
        {
            "project_id": "project-2",
            "source_id": "source-1",
            "target_id": "direction-1",
            "relation_type": "supports",
        },
    ),
    ("remove_record", {"project_id": "project-1", "record_id": "record-1"}),
    ("remove_relation", {"project_id": "project-2", "relation_id": "relation-1"}),
    (
        "local_map",
        {"project_id": "project-1", "query": {"text": "orbit", "limit": 5}},
    ),
)

_MMR_VALUES = {
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
}


class RecordingKernel:
    def __init__(self):
        self.calls = []
        self.record_error = None

    def record(self, project_id, record_type, content, artifact_ids=()):
        if self.record_error is not None:
            raise self.record_error
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

    def __init__(self, operation="record"):
        self.operation = operation

    async def start(self, request):
        return {"value": None}

    async def submit(self, handle, request, emit):
        handle["value"] = request.tools.invoke(
            "kernel",
            self.operation,
            {
                "project_id": "project-1",
                "record_type": "direction",
                "content": {"text": "candidate"},
            },
        )
        return AdapterResult(result_text="recorded")

    async def cancel(self, handle, request):
        return None

    async def close(self):
        return None


class KernelOperationsAdapter(ToolAdapter):
    async def submit(self, handle, request, emit):
        for operation, values in _KERNEL_OPERATIONS:
            request.tools.invoke("kernel", operation, values)
        return AdapterResult(result_text="kernel operations complete")


class MMRAdapter(ToolAdapter):
    def __init__(self):
        self.selection = None

    async def submit(self, handle, request, emit):
        self.selection = request.tools.invoke("brainstorm", "mmr", _MMR_VALUES)
        return AdapterResult(result_text="mmr complete")


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


async def _tool_trace(tmp_path, adapter, kernel, selected):
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch(
        {"adapter": "tool", "tools": selected}, session_id="session-tools"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "run"})
    return await _events(runtime, turn["id"])


def _assert_kernel_operations(kernel):
    assert kernel.calls == [
        ("record", "project-1", "source", {}, ()),
        ("connect", "project-2", "source-1", "direction-1", "supports"),
        ("remove_record", "project-1", "record-1"),
        ("remove_relation", "project-2", "relation-1"),
        ("local_map", "project-1", LocalMapQuery(text="orbit", limit=5)),
    ]


@pytest.mark.asyncio
async def test_adapter_can_use_kernel_tool_record_operation(tmp_path):
    kernel = RecordingKernel()
    adapter = ToolAdapter()
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch(
        {"adapter": "tool", "tools": ["kernel"]}, session_id="session-tools"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "record"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {"status": "completed", "result_text": "recorded"}
    assert kernel.calls == [
        ("record", "project-1", "direction", {"text": "candidate"}, ())
    ]


@pytest.mark.asyncio
async def test_kernel_tool_forwards_project_scoped_operations(tmp_path):
    kernel = RecordingKernel()
    trace = await _tool_trace(tmp_path, KernelOperationsAdapter(), kernel, ["kernel"])
    assert trace[-1]["data"] == {
        "status": "completed",
        "result_text": "kernel operations complete",
    }
    _assert_kernel_operations(kernel)


@pytest.mark.asyncio
async def test_brainstorm_mmr_is_deterministic_and_does_not_touch_kernel(tmp_path):
    kernel = RecordingKernel()
    adapter = MMRAdapter()
    runtime = Runtime(tmp_path, {"tool": adapter}, kernel=kernel)
    run = await runtime.launch(
        {"adapter": "tool", "tools": ["brainstorm"]}, session_id="session-tools"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "select"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {"status": "completed", "result_text": "mmr complete"}
    assert adapter.selection == [
        {"id": "a", "relevance": 0.9},
        {"id": "c", "relevance": 0.8},
    ]
    assert kernel.calls == []


@pytest.mark.asyncio
async def test_kernel_record_key_error_reaches_turn_error(tmp_path):
    kernel = RecordingKernel()
    kernel.record_error = KeyError("record")
    runtime = Runtime(tmp_path, {"tool": ToolAdapter()}, kernel=kernel)
    run = await runtime.launch(
        {"adapter": "tool", "tools": ["kernel"]}, session_id="session-tools"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "record"})
    trace = await _events(runtime, turn["id"])
    assert trace[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "'record'",
    }


@pytest.mark.asyncio
async def test_unknown_kernel_operation_has_explicit_error(tmp_path):
    kernel = RecordingKernel()
    runtime = Runtime(tmp_path, {"tool": ToolAdapter("missing")}, kernel=kernel)
    run = await runtime.launch(
        {"adapter": "tool", "tools": ["kernel"]}, session_id="session-tools"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "unknown"})
    trace = await _events(runtime, turn["id"])
    assert trace[-1]["data"]["error"] == "'unknown tool operation: kernel.missing'"

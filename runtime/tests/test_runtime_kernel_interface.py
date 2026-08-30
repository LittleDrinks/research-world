import pytest

from server.kernel_interface import create_kernel

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


def _read_local_map(tools, project_id):
    return tools.invoke(
        "kernel",
        "local_map",
        {"project_id": project_id, "query": {"text": "shared", "limit": 5}},
    )


def _connect_foreign_record(tools, project_id, source_id, target_id):
    try:
        tools.invoke(
            "kernel",
            "connect",
            {
                "project_id": project_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": "supports",
            },
        )
    except PermissionError as error:
        return error
    return None


class KernelIntegrationAdapter:
    adapter_id = "integration"
    supports_multiple_writers = True

    def __init__(self, project, foreign, record):
        self.project = project
        self.foreign = foreign
        self.record = record
        self.local_map = None
        self.cross_project_error = None

    async def start(self, request):
        return request

    async def submit(self, handle, request, emit):
        tools = request.tools
        self.local_map = _read_local_map(tools, self.project.id)
        self.cross_project_error = _connect_foreign_record(
            tools, self.project.id, self.record.id, self.foreign.id
        )
        return AdapterResult(result_text="kernel integration complete")

    async def cancel(self, handle, request):
        return None


class InvalidLocalMapAdapter:
    adapter_id = "invalid"
    supports_multiple_writers = True

    def __init__(self, project_id, record_id):
        self.project_id = project_id
        self.record_id = record_id

    async def start(self, request):
        return request

    async def submit(self, handle, request, emit):
        request.tools.invoke(
            "kernel",
            "local_map",
            {
                "project_id": self.project_id,
                "query": {"text": "shared", "record_id": self.record_id},
            },
        )
        return AdapterResult(result_text="unreachable")

    async def cancel(self, handle, request):
        return None


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


def _kernel_fixture(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project("Orbit study", "Why are orbits stable?")
    foreign_project = kernel.create_project("Star study", "Why do stars shine?")
    record = kernel.record(project.id, "source", {"text": "shared evidence"})
    foreign_record = kernel.record(
        foreign_project.id, "source", {"text": "shared evidence"}
    )
    return kernel, project, foreign_record, record


@pytest.mark.asyncio
async def test_runtime_kernel_tool_uses_public_project_scoped_interface(tmp_path):
    kernel, project, foreign_record, record = _kernel_fixture(tmp_path)
    adapter = KernelIntegrationAdapter(project, foreign_record, record)
    runtime = Runtime(tmp_path / "runtime", {"integration": adapter}, kernel=kernel)
    run = await runtime.launch({"adapter": "integration", "tools": ["kernel"]})
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "inspect"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {
        "status": "completed",
        "result_text": "kernel integration complete",
    }
    assert adapter.local_map.records == (record,)
    assert isinstance(adapter.cross_project_error, PermissionError)


@pytest.mark.asyncio
async def test_runtime_kernel_tool_preserves_local_map_domain_errors(tmp_path):
    kernel, project, _, record = _kernel_fixture(tmp_path)
    adapter = InvalidLocalMapAdapter(project.id, record.id)
    runtime = Runtime(tmp_path / "runtime", {"invalid": adapter}, kernel=kernel)
    run = await runtime.launch({"adapter": "invalid", "tools": ["kernel"]})
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "inspect"})

    trace = await _events(runtime, turn["id"])

    assert trace[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "local map query requires text or record id",
    }

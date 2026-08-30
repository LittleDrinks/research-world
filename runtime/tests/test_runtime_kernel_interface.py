import pytest

from server.kernel_interface import LocalMapQuery, create_kernel

from runtime.runtime import AdapterResult, Runtime


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
        self.local_map = tools.invoke(
            "kernel",
            "local_map",
            {
                "project_id": self.project.id,
                "query": LocalMapQuery(text="shared", limit=5),
            },
        )
        try:
            tools.invoke(
                "kernel",
                "connect",
                {
                    "project_id": self.project.id,
                    "source_id": self.record.id,
                    "target_id": self.foreign.id,
                    "relation_type": "supports",
                },
            )
        except PermissionError as error:
            self.cross_project_error = error
        return AdapterResult(result_text="kernel integration complete")

    async def cancel(self, handle, request):
        return None


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


@pytest.mark.asyncio
async def test_runtime_kernel_tool_uses_public_project_scoped_interface(tmp_path):
    kernel = create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project("Orbit study", "Why are orbits stable?")
    foreign_project = kernel.create_project("Star study", "Why do stars shine?")
    record = kernel.record(project.id, "source", {"text": "shared evidence"})
    foreign_record = kernel.record(
        foreign_project.id, "source", {"text": "shared evidence"}
    )
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

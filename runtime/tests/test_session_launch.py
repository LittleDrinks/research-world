import asyncio

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


SPEC = {"id": "main", "adapter": "fake"}


class HoldAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.release = asyncio.Event()
        self.calls = []

    async def start(self, request):
        self.calls.append("start")
        return object()

    async def submit(self, handle, request, emit):
        self.calls.append("submit")
        await self.release.wait()
        return AdapterResult(status="cancelled")

    async def cancel(self, handle, request):
        self.calls.append("cancel")
        self.release.set()


@pytest.mark.asyncio
async def test_launch_recovers_session_root_run_in_fresh_runtime(tmp_path):
    original = await Runtime(tmp_path, {"fake": HoldAdapter()}).launch(
        SPEC, session_id="session-200"
    )
    restarted = Runtime(tmp_path, {"fake": HoldAdapter()})

    recovered = await restarted.launch(SPEC, session_id="session-200")

    assert recovered["id"] == original["id"]
    assert recovered["session_id"] == "session-200"


@pytest.mark.asyncio
async def test_launch_snapshot_conflict_fails_before_adapter_or_trace(tmp_path):
    adapter = HoldAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    original = await runtime.launch(SPEC, session_id="session-200")

    with pytest.raises(ValueError, match="session launch conflicts"):
        await runtime.launch(
            {**SPEC, "adapter": "missing"}, session_id="session-200"
        )

    assert adapter.calls == []
    assert (await runtime.launch(SPEC, session_id="session-200"))["id"] == original["id"]


@pytest.mark.asyncio
async def test_child_run_has_no_session_binding_or_session_index_claim(tmp_path):
    adapter = HoldAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    parent = await runtime.launch(SPEC, session_id="session-200")
    parent_turn = await runtime.submit(parent["session_id"], {"id": "parent", "content": "delegate"})
    child = await runtime.delegate(
        parent["id"], {"id": "child", "adapter": "fake"}, parent_turn_id=parent_turn["id"]
    )

    assert child["session_id"] is None
    with pytest.raises(KeyError, match="session not found"):
        await runtime.submit(child["id"], {"id": "child", "content": "work"})
    assert adapter.calls == []
    restarted = Runtime(tmp_path, {"fake": HoldAdapter()})
    recovered = await restarted.launch(SPEC, session_id="session-200")
    assert recovered["id"] == parent["id"]
    await runtime.cancel(parent_turn["id"])

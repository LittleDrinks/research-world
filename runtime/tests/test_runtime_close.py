import asyncio

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


class ControlledAdapter:
    adapter_id = "controlled"
    supports_multiple_writers = True

    def __init__(self, adapter_id="controlled"):
        self.adapter_id = adapter_id
        self.close_calls = 0
        self.close_error = None
        self.close_gate = None
        self.close_started = asyncio.Event()
        self.cancel_calls = []
        self.submit_gate = asyncio.Event()
        self.submit_started = asyncio.Event()
        self.submit_stopped = asyncio.Event()
        self.submit_count = 0
        self.all_submits_started = asyncio.Event()
        self.start_gate = None
        self.start_cancel_release = None
        self.start_entered = asyncio.Event()
        self.start_cancelled = asyncio.Event()
        self.start_stopped = asyncio.Event()

    async def start(self, request):
        self.start_entered.set()
        try:
            if self.start_gate is not None:
                await self.start_gate.wait()
            return object()
        except asyncio.CancelledError:
            self.start_cancelled.set()
            if self.start_cancel_release is not None:
                await self.start_cancel_release.wait()
            raise
        finally:
            self.start_stopped.set()

    async def submit(self, handle, request, emit):
        self.submit_count += 1
        if self.submit_count == 2:
            self.all_submits_started.set()
        self.submit_started.set()
        try:
            await self.submit_gate.wait()
            status = "cancelled" if self.cancel_calls else "completed"
            return AdapterResult(status=status, result_text="done")
        finally:
            self.submit_stopped.set()

    async def cancel(self, handle, request):
        self.cancel_calls.append(request.turn_id)
        self.submit_gate.set()

    async def close(self):
        self.close_calls += 1
        self.close_started.set()
        if self.close_gate is not None:
            await self.close_gate.wait()
        if self.close_error is not None:
            raise self.close_error


def _owned_tasks():
    return asyncio.all_tasks() - {asyncio.current_task()}


async def _close_after_submit(runtime, adapter):
    owned_tasks = _owned_tasks()
    closing = asyncio.create_task(runtime.close())
    try:
        await asyncio.wait_for(asyncio.shield(closing), timeout=1)
    finally:
        adapter.submit_gate.set()
        await asyncio.wait_for(closing, timeout=1)
    return owned_tasks


async def _close_after_start_cancel(runtime, adapter):
    owned_tasks = _owned_tasks()
    closing = asyncio.create_task(runtime.close())
    await adapter.start_cancelled.wait()
    assert not closing.done()
    adapter.start_cancel_release.set()
    await closing
    return owned_tasks


async def _running_turns(tmp_path):
    adapter = ControlledAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    run = await runtime.launch(
        {"id": "main", "adapter": "controlled"}, session_id="session-main"
    )
    first = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})
    second = await runtime.submit(run["session_id"], {"id": "message-2", "content": "two"})
    await adapter.all_submits_started.wait()
    return runtime, adapter, first, second, _owned_tasks()


@pytest.mark.asyncio
async def test_close_rejects_new_launch_and_submit(tmp_path):
    adapter = ControlledAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    run = await runtime.launch({"id": "main", "adapter": "controlled"}, session_id="session-main")

    await runtime.close()

    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.launch({"id": "other", "adapter": "controlled"}, session_id="session-other")
    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})


@pytest.mark.asyncio
async def test_close_cancels_active_turn_and_awaits_its_task(tmp_path):
    adapter = ControlledAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    run = await runtime.launch({"id": "main", "adapter": "controlled"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})
    await adapter.submit_started.wait()
    owned_tasks = await _close_after_submit(runtime, adapter)

    observed = [event async for event in runtime.subscribe(turn["id"])]
    assert adapter.cancel_calls == [turn["id"]]
    assert observed[-1]["data"]["status"] == "cancelled"
    assert adapter.submit_stopped.is_set()
    assert adapter.close_calls == 1
    assert not owned_tasks.intersection(asyncio.all_tasks())


@pytest.mark.asyncio
async def test_close_failure_is_explicit_and_lifecycle_stays_closed(tmp_path):
    adapter = ControlledAdapter("failing")
    adapter.close_error = ValueError("adapter close failed")
    other = ControlledAdapter("healthy")
    runtime = Runtime(tmp_path, {"failing": adapter, "healthy": other})

    with pytest.raises(RuntimeError, match="runtime close failed"):
        await runtime.close()
    with pytest.raises(RuntimeError, match="runtime close failed"):
        await runtime.close()
    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.launch({"id": "main", "adapter": "controlled"})

    assert adapter.close_calls == 1
    assert other.close_calls == 1


@pytest.mark.asyncio
async def test_close_waits_for_pending_start_cancellation(tmp_path):
    adapter = ControlledAdapter()
    adapter.start_gate = asyncio.Event()
    adapter.start_cancel_release = asyncio.Event()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    run = await runtime.launch({"id": "main", "adapter": "controlled"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})
    await adapter.start_entered.wait()
    owned_tasks = await _close_after_start_cancel(runtime, adapter)

    observed = [event async for event in runtime.subscribe(turn["id"])]
    assert observed[-1]["data"]["status"] == "cancelled"
    assert adapter.start_stopped.is_set()
    assert adapter.close_calls == 1
    assert not owned_tasks.intersection(asyncio.all_tasks())


@pytest.mark.asyncio
async def test_close_cancels_all_running_turns_and_replays_terminal_trace(tmp_path):
    runtime, adapter, first, second, owned_tasks = await _running_turns(tmp_path)

    await asyncio.gather(runtime.close(), runtime.close())
    first_events = [event async for event in runtime.subscribe(first["id"])]
    second_events = [event async for event in runtime.subscribe(second["id"])]
    restarted_adapter = ControlledAdapter()
    restarted = Runtime(tmp_path, {"controlled": restarted_adapter})
    replayed = [event async for event in restarted.subscribe(first["id"])]
    await restarted.close()

    assert sorted(adapter.cancel_calls) == sorted([first["id"], second["id"]])
    assert first_events[-1]["data"]["status"] == "cancelled"
    assert second_events[-1]["data"]["status"] == "cancelled"
    assert replayed == first_events
    assert not restarted_adapter.start_entered.is_set()
    assert restarted_adapter.submit_count == 0
    assert not owned_tasks.intersection(asyncio.all_tasks())


@pytest.mark.asyncio
async def test_close_rejects_execution_while_adapter_close_is_pending(tmp_path):
    adapter = ControlledAdapter()
    adapter.close_gate = asyncio.Event()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    run = await runtime.launch({"id": "main", "adapter": "controlled"}, session_id="session-main")
    closing = asyncio.create_task(runtime.close())

    await adapter.close_started.wait()
    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.launch({"id": "other", "adapter": "controlled"}, session_id="session-other")
    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})

    adapter.close_gate.set()
    await asyncio.gather(closing, runtime.close())


@pytest.mark.asyncio
async def test_idle_close_is_idempotent_for_each_adapter(tmp_path):
    adapter = ControlledAdapter()
    other = ControlledAdapter("other")
    runtime = Runtime(tmp_path, {"controlled": adapter, "other": other})

    await asyncio.gather(runtime.close(), runtime.close())
    await runtime.close()

    assert adapter.close_calls == 1
    assert other.close_calls == 1

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


_CHILD_TASK_REENTRANT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime
class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.runtime = None
        self.reentrant_error = None
        self.close_calls = 0
    async def start(self, request): return object()
    async def submit(self, handle, request, emit):
        async def close_from_child():
            try: await self.runtime.close()
            except RuntimeError as error: self.reentrant_error = str(error)
        await asyncio.gather(asyncio.create_task(close_from_child()))
        return AdapterResult(result_text="done")
    async def cancel(self, handle, request): return None
    async def close(self): self.close_calls += 1
async def events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]
async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    adapter.runtime = runtime
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})
    observed = await asyncio.wait_for(events(runtime, turn["id"]), timeout=1)
    before_close = adapter.close_calls
    await runtime.close()
    print(json.dumps({"error": adapter.reentrant_error, "before_close": before_close, "after_close": adapter.close_calls, "event": observed[-1]["data"]}))
asyncio.run(main())
'''


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


class ReentrantAdapter(ControlledAdapter):
    def __init__(self):
        super().__init__()
        self.runtime = None
        self.reentrant_error = None

    async def submit(self, handle, request, emit):
        try:
            await self.runtime.close()
        except RuntimeError as error:
            self.reentrant_error = str(error)
        return AdapterResult(result_text="done")


class ReentrantCancelAdapter(ControlledAdapter):
    def __init__(self):
        super().__init__()
        self.runtime = None
        self.reentrant_task = None

    async def cancel(self, handle, request):
        self.reentrant_task = asyncio.create_task(self.runtime.close())
        await super().cancel(handle, request)


class ReentrantCloseAdapter(ControlledAdapter):
    def __init__(self):
        super().__init__()
        self.runtime = None
        self.reentrant_task = None

    async def close(self):
        self.close_calls += 1
        self.close_started.set()
        self.reentrant_task = asyncio.create_task(self.runtime.close())


class MissingCloseAdapter:
    adapter_id = "missing"
    supports_multiple_writers = True

    async def start(self, request):
        return object()

    async def submit(self, handle, request, emit):
        return AdapterResult(result_text="done")

    async def cancel(self, handle, request):
        return None


class SyncCloseAdapter(MissingCloseAdapter):
    adapter_id = "sync"

    def close(self):
        return None


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


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


async def _cancel_twice(task):
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)


@pytest.mark.parametrize(
    "adapter", [MissingCloseAdapter(), SyncCloseAdapter()], ids=["missing", "sync"]
)
def test_runtime_rejects_non_async_close_before_store(tmp_path, adapter):
    with pytest.raises(TypeError, match="adapters must implement RuntimeAdapter"):
        Runtime(tmp_path, {adapter.adapter_id: adapter})
    assert not tuple(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_reentrant_close_fails_before_lifecycle_state_changes(tmp_path):
    adapter = ReentrantAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    adapter.runtime = runtime
    run = await runtime.launch(
        {"id": "main", "adapter": "controlled"}, session_id="session-main"
    )
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})

    observed = await asyncio.wait_for(_events(runtime, turn["id"]), timeout=1)
    assert adapter.reentrant_error == "runtime close cannot run from an active turn"
    assert observed[-1]["data"] == {"status": "completed", "result_text": "done"}
    await runtime.launch({"id": "other", "adapter": "controlled"}, session_id="session-other")
    await runtime.close()
    assert adapter.close_calls == 1


def test_child_task_reentrant_close_fails_before_lifecycle_state_changes(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", _CHILD_TASK_REENTRANT_PROCESS, str(tmp_path)],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        timeout=1,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "error": "runtime close cannot run from an active turn",
        "before_close": 0,
        "after_close": 1,
        "event": {"status": "completed", "result_text": "done"},
    }


@pytest.mark.asyncio
async def test_reentrant_cancel_close_fails_before_self_wait(tmp_path):
    adapter = ReentrantCancelAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    adapter.runtime = runtime
    run = await runtime.launch({"id": "main", "adapter": "controlled"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "message-1", "content": "one"})
    await adapter.submit_started.wait()
    owned_tasks = _owned_tasks()

    await runtime.close()

    with pytest.raises(RuntimeError, match="runtime close cannot run from an active turn"):
        await adapter.reentrant_task
    assert (await _events(runtime, turn["id"]))[-1]["data"]["status"] == "cancelled"
    assert not owned_tasks.intersection(asyncio.all_tasks())


@pytest.mark.asyncio
async def test_reentrant_adapter_close_fails_before_self_wait(tmp_path):
    adapter = ReentrantCloseAdapter()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    adapter.runtime = runtime

    await runtime.close()

    with pytest.raises(RuntimeError, match="runtime close cannot run from an active turn"):
        await adapter.reentrant_task
    assert adapter.close_calls == 1


@pytest.mark.asyncio
async def test_cancelled_close_caller_waits_for_shutdown_and_does_not_retry(tmp_path):
    adapter = ControlledAdapter()
    adapter.close_gate = asyncio.Event()
    runtime = Runtime(tmp_path, {"controlled": adapter})
    closing = asyncio.create_task(runtime.close())
    await adapter.close_started.wait()
    owned_tasks = _owned_tasks()

    await _cancel_twice(closing)
    assert not closing.done()
    adapter.close_gate.set()
    with pytest.raises(asyncio.CancelledError):
        await closing

    assert not owned_tasks.intersection(asyncio.all_tasks())
    await runtime.close()
    assert adapter.close_calls == 1


@pytest.mark.asyncio
async def test_cancelled_close_caller_preserves_cancellation_on_failure(tmp_path):
    adapter = ControlledAdapter()
    adapter.close_gate = asyncio.Event()
    adapter.close_error = ValueError("adapter close failed")
    runtime = Runtime(tmp_path, {"controlled": adapter})
    closing = asyncio.create_task(runtime.close())
    await adapter.close_started.wait()
    await _cancel_twice(closing)
    assert not closing.done()

    adapter.close_gate.set()
    with pytest.raises(asyncio.CancelledError):
        await closing
    with pytest.raises(RuntimeError, match="runtime close failed"):
        await runtime.close()
    assert adapter.close_calls == 1


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

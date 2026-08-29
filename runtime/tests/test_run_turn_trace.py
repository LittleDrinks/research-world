import asyncio
from dataclasses import dataclass

import pytest

from runtime import Runtime


@dataclass
class FakeHandle:
    request: object
    released: asyncio.Event
    output: str = ""
    cancelled: bool = False


class FakeAdapter:
    adapter_id = "fake"
    supports_multiple_writers = False

    def __init__(self):
        self._handles = {}

    async def start(self, request):
        handle = FakeHandle(request, asyncio.Event())
        self._handles[request.turn_id] = handle
        return handle

    async def submit(self, handle, request, emit):
        await handle.released.wait()
        if handle.cancelled:
            return {"status": "cancelled"}
        await emit({"type": "delta", "data": {"text": handle.output}})
        return {"status": "completed", "result_text": handle.output}

    async def cancel(self, handle):
        handle.cancelled = True
        handle.released.set()

    async def wait_for_handles(self, count=2):
        await asyncio.wait_for(self._wait_for_handles(count), timeout=1)

    async def _wait_for_handles(self, count):
        while self.handle_count() < count:
            await asyncio.sleep(0)

    def complete(self, turn_id, output):
        handle = self._handles[turn_id]
        handle.output = output
        handle.released.set()

    def request_for(self, turn_id):
        return self._handles[turn_id].request

    def handle_count(self):
        return len(self._handles)

    def was_cancelled(self, turn_id):
        return self._handles[turn_id].cancelled


def message(message_id, content):
    return {"id": message_id, "content": content}


async def events(runtime, turn_id, after_seq=-1):
    return [event async for event in runtime.subscribe(turn_id, after_seq)]


async def launch(runtime, agent_id="main"):
    return await runtime.launch({"id": agent_id, "adapter": "fake"})


@pytest.mark.asyncio
@pytest.mark.parametrize("child", [False, True])
async def test_main_and_child_runs_keep_concurrent_turns_independent(tmp_path, child):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    parent = await launch(runtime)
    run = (
        await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"})
        if child
        else parent
    )

    first = await runtime.submit(run["id"], message("m1", "one"))
    second = await runtime.submit(run["id"], message("m2", "two"))
    await adapter.wait_for_handles()

    assert adapter.request_for(first["id"]).context == ()
    assert adapter.request_for(second["id"]).context == ()

    adapter.complete(second["id"], "answer two")
    adapter.complete(first["id"], "answer one")
    first_events, second_events = await asyncio.gather(
        events(runtime, first["id"]), events(runtime, second["id"])
    )

    assert first_events[-1]["data"] == {
        "status": "completed",
        "result_text": "answer one",
    }
    assert second_events[-1]["data"] == {
        "status": "completed",
        "result_text": "answer two",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("child", [False, True])
async def test_main_and_child_runs_can_cancel_one_turn(tmp_path, child):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    parent = await launch(runtime)
    run = (
        await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"})
        if child
        else parent
    )

    cancelled = await runtime.submit(run["id"], message("cancel", "stop"))
    alive = await runtime.submit(run["id"], message("alive", "continue"))
    await adapter.wait_for_handles()

    result = await runtime.cancel(cancelled["id"])
    adapter.complete(alive["id"], "still running")
    cancelled_events, alive_events = await asyncio.gather(
        events(runtime, cancelled["id"]), events(runtime, alive["id"])
    )

    assert result["status"] == "cancelled"
    assert adapter.was_cancelled(cancelled["id"]) is True
    assert cancelled_events[-1]["data"]["status"] == "cancelled"
    assert alive_events[-1]["data"] == {
        "status": "completed",
        "result_text": "still running",
    }
    assert sum(event["type"] == "turn_end" for event in cancelled_events) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("child", [False, True])
async def test_main_and_child_runs_reconnect_from_last_sequence(tmp_path, child):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    parent = await launch(runtime)
    run = (
        await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"})
        if child
        else parent
    )
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)

    subscription = runtime.subscribe(turn["id"])
    started = await anext(subscription)
    await subscription.aclose()
    adapter.complete(turn["id"], "done")

    remaining = await events(runtime, turn["id"], started["seq"])

    assert [event["type"] for event in remaining] == ["delta", "turn_end"]
    assert adapter.handle_count() == 1


@pytest.mark.asyncio
async def test_submit_is_idempotent_for_the_kernel_message_id(tmp_path):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    run = await launch(runtime)

    first = await runtime.submit(run["id"], message("same", "first"))
    duplicate = await runtime.submit(run["id"], message("same", "changed"))
    await adapter.wait_for_handles(1)

    assert duplicate == first
    assert adapter.handle_count() == 1
    adapter.complete(first["id"], "done")
    completed = await events(runtime, first["id"])
    repeated = await runtime.submit(run["id"], message("same", "changed again"))
    assert repeated["id"] == first["id"]
    assert repeated["status"] == completed[-1]["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_concurrent_duplicate_submits_create_one_turn(tmp_path):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    run = await launch(runtime)

    first, duplicate = await asyncio.gather(
        runtime.submit(run["id"], message("same", "first")),
        runtime.submit(run["id"], message("same", "first")),
    )

    assert duplicate == first
    await adapter.wait_for_handles(1)
    assert adapter.handle_count() == 1
    adapter.complete(first["id"], "done")
    await events(runtime, first["id"])


@pytest.mark.asyncio
async def test_submit_freezes_only_completed_context(tmp_path):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    run = await launch(runtime)
    first = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    adapter.complete(first["id"], "answer one")
    await events(runtime, first["id"])

    second = await runtime.submit(run["id"], message("m2", "two"))
    third = await runtime.submit(run["id"], message("m3", "three"))
    await adapter.wait_for_handles(3)

    expected = (
        {"role": "user", "message_id": "m1", "content": "one"},
        {"role": "assistant", "content": "answer one"},
    )
    assert adapter.request_for(second["id"]).context == expected
    assert adapter.request_for(third["id"]).context == expected


@pytest.mark.asyncio
async def test_trace_is_replayable_after_runtime_restarts(tmp_path):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters=[adapter])
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    adapter.complete(turn["id"], "done")
    original = await events(runtime, turn["id"])

    restarted_adapter = FakeAdapter()
    restarted = Runtime(data_root=tmp_path, adapters=[restarted_adapter])
    replayed = await events(restarted, turn["id"])

    assert replayed == original
    assert restarted_adapter.handle_count() == 0


@pytest.mark.asyncio
async def test_launch_freezes_agent_snapshot_and_delegate_links_parent(tmp_path):
    adapter = FakeAdapter()
    runtime = Runtime(data_root=tmp_path, adapters={"fake": adapter})
    spec = {"id": "main", "adapter": "fake", "params": {"mode": "fast"}}

    parent = await runtime.launch(spec, session_id="session-1")
    spec["params"]["mode"] = "changed"
    child = await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"})

    assert parent["agent_snapshot"]["params"] == {"mode": "fast"}
    assert parent["session_id"] == "session-1"
    assert child["parent_run_id"] == parent["id"]

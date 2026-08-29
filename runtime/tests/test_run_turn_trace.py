import asyncio
from dataclasses import dataclass

import pytest

from runtime.runtime import AdapterResult, Runtime

_UNSET = object()


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
        self.event = _UNSET
        self.result = _UNSET

    async def start(self, request):
        handle = FakeHandle(request, asyncio.Event())
        self._handles[request.turn_id] = handle
        return handle

    async def submit(self, handle, request, emit):
        await handle.released.wait()
        if handle.cancelled:
            return AdapterResult(status="cancelled")
        event = self.event
        if event is _UNSET:
            event = {"type": "delta", "data": {"text": handle.output}}
        await emit(event)
        if self.result is _UNSET:
            return AdapterResult(result_text=handle.output)
        return self.result

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


def _make_runtime(tmp_path):
    adapter = FakeAdapter()
    return Runtime(data_root=tmp_path, adapters={"fake": adapter}), adapter


async def _run_for(runtime, child):
    parent = await launch(runtime)
    if child:
        return await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"})
    return parent


async def _submit_concurrent(runtime, adapter, run):
    first = await runtime.submit(run["id"], message("m1", "one"))
    second = await runtime.submit(run["id"], message("m2", "two"))
    await adapter.wait_for_handles()
    return first, second


async def _submit_cancel_pair(runtime, adapter, run):
    cancelled = await runtime.submit(run["id"], message("cancel", "stop"))
    alive = await runtime.submit(run["id"], message("alive", "continue"))
    await adapter.wait_for_handles()
    return cancelled, alive


async def _complete_concurrent(runtime, adapter, first, second):
    adapter.complete(second["id"], "answer two")
    adapter.complete(first["id"], "answer one")
    return await asyncio.gather(
        events(runtime, first["id"]), events(runtime, second["id"])
    )


async def _adapter_trace(tmp_path, *, event=_UNSET, result=_UNSET):
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, False)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    if event is not _UNSET:
        adapter.event = event
    if result is not _UNSET:
        adapter.result = result
    adapter.complete(turn["id"], "done")
    return await events(runtime, turn["id"])


def _assert_empty_context(adapter, first, second):
    assert adapter.request_for(first["id"]).context == ()
    assert adapter.request_for(second["id"]).context == ()


@pytest.mark.parametrize("adapters", ["list", "single"])
def test_runtime_requires_explicit_adapter_mapping(tmp_path, adapters):
    adapter = FakeAdapter()
    value = [adapter] if adapters == "list" else adapter
    with pytest.raises(TypeError):
        Runtime(data_root=tmp_path, adapters=value)


@pytest.mark.parametrize(
    ("key", "adapter_id"), [("alias", "fake"), ("fake", "")]
)
def test_runtime_requires_matching_nonempty_adapter_id(tmp_path, key, adapter_id):
    adapter = FakeAdapter()
    adapter.adapter_id = adapter_id
    with pytest.raises((TypeError, ValueError)):
        Runtime(data_root=tmp_path, adapters={key: adapter})


@pytest.mark.parametrize("method", ["start", "submit", "cancel"])
def test_runtime_requires_async_adapter_methods(tmp_path, method):
    adapter = FakeAdapter()
    setattr(adapter, method, lambda *args: None)
    with pytest.raises(TypeError):
        Runtime(data_root=tmp_path, adapters={"fake": adapter})


@pytest.mark.parametrize("data_root", [None, "string-path"])
def test_runtime_requires_persistent_path(tmp_path, data_root):
    value = tmp_path if data_root == "string-path" else data_root
    if data_root == "string-path":
        value = str(value)
    with pytest.raises(TypeError):
        Runtime(data_root=value, adapters={"fake": FakeAdapter()})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "spec", [{}, {"runtime": {"id": "fake"}}, {"adapter": "missing"}]
)
async def test_launch_requires_explicit_adapter_id(tmp_path, spec):
    runtime, adapter = _make_runtime(tmp_path)
    with pytest.raises((TypeError, ValueError)):
        await runtime.launch(spec)
    assert adapter.handle_count() == 0


@pytest.mark.asyncio
async def test_launch_cannot_create_child_with_parent_argument(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    parent = await launch(runtime)
    with pytest.raises(TypeError):
        await runtime.launch({"adapter": "fake"}, parent_run_id=parent["id"])
    assert adapter.handle_count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("submitted", "content"),
    [
        ("m1", "one"),
        ({"message_id": "m1", "content": "one"}, None),
        ({"id": "m1", "input": "one"}, None),
        ({"id": "m1", "content": "one", "message_id": "old"}, None),
    ],
)
async def test_submit_requires_persisted_message_shape(tmp_path, submitted, content):
    runtime, adapter = _make_runtime(tmp_path)
    run = await launch(runtime)
    with pytest.raises((TypeError, ValueError)):
        if content is None:
            await runtime.submit(run["id"], submitted)
        else:
            await runtime.submit(run["id"], submitted, content)
    assert adapter.handle_count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event",
    [
        None,
        "delta",
        {},
        {"type": "delta"},
        {"type": "", "data": {}},
        {"type": "delta", "data": "raw"},
        {"text": "raw"},
        {"type": "delta", "data": {}, "extra": True},
    ],
)
async def test_adapter_events_require_normalized_shape(tmp_path, event):
    trace = await _adapter_trace(tmp_path, event=event)
    assert trace[-1]["data"]["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result", [None, "done", {"status": "completed", "result_text": "done"},
                {"output": "done"}, {"result": "done"}],
)
async def test_adapter_results_require_adapter_result(tmp_path, result):
    trace = await _adapter_trace(tmp_path, result=result)
    assert trace[-1]["data"]["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize("child", [False, True])
async def test_main_and_child_runs_keep_concurrent_turns_independent(tmp_path, child):
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, child)
    first, second = await _submit_concurrent(runtime, adapter, run)

    _assert_empty_context(adapter, first, second)

    first_events, second_events = await _complete_concurrent(
        runtime, adapter, first, second
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
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, child)
    cancelled, alive = await _submit_cancel_pair(runtime, adapter, run)

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
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, child)
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
async def test_subscription_drains_events_written_while_paused(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    subscription = runtime.subscribe(turn["id"])

    started = await anext(subscription)
    adapter.complete(turn["id"], "done")
    await asyncio.sleep(0)
    delta = await anext(subscription)
    ended = await anext(subscription)
    await subscription.aclose()

    assert started["type"] == "turn_start"
    assert delta["type"] == "delta"
    assert ended["type"] == "turn_end"


@pytest.mark.asyncio
@pytest.mark.parametrize("child", [False, True])
async def test_submit_is_idempotent_for_the_kernel_message_id(tmp_path, child):
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, child)

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
@pytest.mark.parametrize("child", [False, True])
async def test_concurrent_duplicate_submits_create_one_turn(tmp_path, child):
    runtime, adapter = _make_runtime(tmp_path)
    run = await _run_for(runtime, child)

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
    runtime, adapter = _make_runtime(tmp_path)
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
    runtime, adapter = _make_runtime(tmp_path)
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    adapter.complete(turn["id"], "done")
    original = await events(runtime, turn["id"])

    restarted_adapter = FakeAdapter()
    restarted = Runtime(data_root=tmp_path, adapters={"fake": restarted_adapter})
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

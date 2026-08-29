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
        self.start_gate = None
        self.start_cancel_release = None
        self.start_entered = asyncio.Event()
        self.start_cancelled = asyncio.Event()
        self.start_stopped = asyncio.Event()
        self.submit_stopped = asyncio.Event()
        self.cancel_error = None
        self.cancel_result = None
        self.submit_cancel_error = None
        self.start_cancel_error = None

    async def start(self, request):
        self.start_entered.set()
        try:
            if self.start_gate is not None:
                await self.start_gate.wait()
            handle = FakeHandle(request, asyncio.Event())
            self._handles[request.turn_id] = handle
            return handle
        except asyncio.CancelledError:
            self.start_cancelled.set()
            if self.start_cancel_release is not None:
                await self.start_cancel_release.wait()
            if self.start_cancel_error is not None:
                raise self.start_cancel_error
            raise
        finally:
            self.start_stopped.set()

    async def submit(self, handle, request, emit):
        try:
            await handle.released.wait()
            if handle.cancelled:
                if self.submit_cancel_error is not None:
                    raise self.submit_cancel_error
                return self.cancel_result or AdapterResult(status="cancelled")
            event = self.event
            if event is _UNSET:
                event = {"type": "delta", "data": {"text": handle.output}}
            await emit(event)
            if self.result is _UNSET:
                return AdapterResult(result_text=handle.output)
            return self.result
        finally:
            self.submit_stopped.set()

    async def cancel(self, handle):
        if self.cancel_error is not None:
            raise self.cancel_error
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


class SharedHandleAdapter(FakeAdapter):
    supports_multiple_writers = False

    def __init__(self):
        super().__init__()
        self.shared_handle = FakeHandle(None, asyncio.Event())

    async def start(self, request):
        self._handles[request.turn_id] = self.shared_handle
        self.shared_handle.request = request
        return self.shared_handle


def message(message_id, content):
    return {"id": message_id, "content": content}


async def _cancelled_adapter_call(*args):
    raise asyncio.CancelledError("adapter operation cancelled unexpectedly")


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


async def _blocked_start_turn(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.start_gate = asyncio.Event()
    adapter.start_cancel_release = asyncio.Event()
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await asyncio.wait_for(adapter.start_entered.wait(), timeout=1)
    return runtime, adapter, turn


async def _begin_cancel(runtime, turn):
    subscription = runtime.subscribe(turn["id"])
    assert (await anext(subscription))["type"] == "turn_start"
    cancellation = asyncio.create_task(runtime.cancel(turn["id"]))
    return subscription, cancellation


async def _wait_for_start_cancel(adapter, cancellation, subscription):
    try:
        await asyncio.wait_for(adapter.start_cancelled.wait(), timeout=1)
    except asyncio.TimeoutError:
        adapter.start_gate.set()
        await asyncio.wait_for(adapter.start_stopped.wait(), timeout=1)
        await cancellation
        await subscription.aclose()
        raise AssertionError("Runtime did not cancel pending adapter start")


async def _terminal_events(runtime, turn_id):
    return await asyncio.wait_for(events(runtime, turn_id), timeout=1)


async def _cancel_with_cancelled_adapter_cleanup(runtime, adapter, turn):
    try:
        return await runtime.cancel(turn["id"])
    except asyncio.CancelledError:
        adapter.complete(turn["id"], "cleanup")
        await asyncio.wait_for(adapter.submit_stopped.wait(), timeout=1)
        return None


async def _trigger_unexpected_cancel(runtime, adapter, turn, method):
    if method == "cancel":
        await adapter.wait_for_handles(1)
        setattr(adapter, method, _cancelled_adapter_call)
        return await _cancel_with_cancelled_adapter_cleanup(runtime, adapter, turn)
    await _terminal_events(runtime, turn["id"])
    return await runtime.submit(turn["run_id"], message("m1", "again"))


async def _pending_terminal(subscription):
    terminal = asyncio.create_task(anext(subscription))
    await asyncio.sleep(0)
    return terminal


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
async def test_cancel_waits_for_blocked_adapter_start(tmp_path):
    runtime, adapter, turn = await _blocked_start_turn(tmp_path)
    subscription, cancellation = await _begin_cancel(runtime, turn)
    await _wait_for_start_cancel(adapter, cancellation, subscription)
    terminal = await _pending_terminal(subscription)
    assert not terminal.done()
    adapter.start_cancel_release.set()
    result = await cancellation
    ended = await terminal
    await subscription.aclose()
    assert result["status"] == ended["data"]["status"] == "cancelled"
    assert adapter.start_stopped.is_set()


@pytest.mark.asyncio
async def test_cancel_start_cleanup_failure_emits_error(tmp_path):
    runtime, adapter, turn = await _blocked_start_turn(tmp_path)
    adapter.start_cancel_error = RuntimeError("adapter start cleanup failed")
    _subscription, cancellation = await _begin_cancel(runtime, turn)
    await _wait_for_start_cancel(adapter, cancellation, _subscription)
    adapter.start_cancel_release.set()
    result = await cancellation
    await _subscription.aclose()
    observed = await events(runtime, turn["id"])
    assert result["status"] == observed[-1]["data"]["status"] == "error"
    assert observed[-1]["data"]["error"] == "adapter start cleanup failed"


@pytest.mark.asyncio
async def test_cancel_failure_emits_one_error_terminal(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.cancel_error = RuntimeError("adapter cancel failed")
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    result = await runtime.cancel(turn["id"])
    observed = await events(runtime, turn["id"])
    terminals = [event for event in observed if event["type"] == "turn_end"]
    assert result["status"] == "error"
    assert adapter.submit_stopped.is_set()
    assert len(terminals) == 1
    assert terminals[0]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "adapter cancel failed",
    }


@pytest.mark.asyncio
async def test_cancel_preserves_active_adapter_error(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.cancel_result = AdapterResult(status="error")
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)

    result = await runtime.cancel(turn["id"])
    observed = await events(runtime, turn["id"])
    terminals = [event for event in observed if event["type"] == "turn_end"]

    assert result["status"] == "error"
    assert adapter.submit_stopped.is_set()
    assert len(terminals) == 1
    assert terminals[0]["data"]["status"] == "error"


@pytest.mark.asyncio
async def test_adapter_submit_cancelled_after_runtime_cancel_is_error(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.submit_cancel_error = asyncio.CancelledError("adapter submit cancelled")
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)

    result = await runtime.cancel(turn["id"])
    observed = await events(runtime, turn["id"])
    terminals = [event for event in observed if event["type"] == "turn_end"]

    assert result["status"] == "error"
    assert len(terminals) == 1
    assert terminals[0]["data"]["error"] == "adapter submit cancelled"


@pytest.mark.asyncio
async def test_non_serializable_result_text_is_error(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.result = AdapterResult(result_text=object())
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    adapter.complete(turn["id"], "done")

    observed = await _terminal_events(runtime, turn["id"])
    repeated = await runtime.submit(run["id"], message("m1", "again"))
    terminals = [event for event in observed if event["type"] == "turn_end"]

    assert repeated["status"] == "error"
    assert len(terminals) == 1
    assert terminals[0]["data"]["status"] == "error"


async def _shared_handle_outcomes(runtime, run, first, second):
    second_events = await _terminal_events(runtime, second["id"])
    second_view = await runtime.submit(run["id"], message("m2", "again"))
    first_result = await runtime.cancel(first["id"])
    first_events = await events(runtime, first["id"])
    return (
        first_result,
        second_view,
        [event for event in first_events if event["type"] == "turn_end"],
        [event for event in second_events if event["type"] == "turn_end"],
    )


@pytest.mark.asyncio
async def test_non_multi_writer_handle_reuse_is_rejected(tmp_path):
    adapter = SharedHandleAdapter()
    runtime = Runtime(data_root=tmp_path, adapters={"fake": adapter})
    run = await launch(runtime)
    first, second = await asyncio.gather(
        runtime.submit(run["id"], message("m1", "one")),
        runtime.submit(run["id"], message("m2", "two")),
    )

    first_result, second_view, first_terminals, second_terminals = (
        await _shared_handle_outcomes(runtime, run, first, second)
    )

    assert first_result["status"] == "cancelled"
    assert second_view["status"] == "error"
    assert first_terminals[-1]["data"]["status"] == "cancelled"
    assert second_terminals[-1]["data"]["status"] == "error"
    assert len(first_terminals) == len(second_terminals) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["start", "submit", "cancel"])
async def test_unexpected_adapter_cancelled_error_is_terminal(tmp_path, method):
    runtime, adapter = _make_runtime(tmp_path)
    run = await launch(runtime)
    if method != "cancel":
        setattr(adapter, method, _cancelled_adapter_call)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    result = await _trigger_unexpected_cancel(runtime, adapter, turn, method)
    observed = await _terminal_events(runtime, turn["id"])
    terminals = [event for event in observed if event["type"] == "turn_end"]

    assert result is not None
    assert result["status"] == "error"
    assert len(terminals) == 1
    assert terminals[0]["data"]["status"] == "error"


@pytest.mark.asyncio
async def test_concurrent_cancel_calls_share_one_terminal(tmp_path):
    runtime, adapter = _make_runtime(tmp_path)
    adapter.cancel_error = RuntimeError("adapter cancel failed")
    run = await launch(runtime)
    turn = await runtime.submit(run["id"], message("m1", "one"))
    await adapter.wait_for_handles(1)
    results = await asyncio.gather(
        runtime.cancel(turn["id"]), runtime.cancel(turn["id"])
    )
    observed = await events(runtime, turn["id"])
    terminals = [event for event in observed if event["type"] == "turn_end"]
    assert [result["status"] for result in results] == ["error", "error"]
    assert len(terminals) == 1
    assert terminals[0]["data"]["status"] == "error"


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

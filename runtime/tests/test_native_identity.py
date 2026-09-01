import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


_RUNTIME_ROOT = Path(__file__).parents[1]
_IDENTITY = {"session_id": "opaque-session"}
_ONE_CHARACTER_IDENTITY = {"session_id": "a"}
_INVALID_IDENTITIES = [
    {"private_key": "secret"},
    {"client_secret_value": "secret"},
    {"api_token": "secret"},
    {"model_token": "secret"},
    {"nested": {"session_id": "opaque-session"}},
    {"adapter_id": "fake", "value": _IDENTITY},
    "opaque-session",
    [],
    {"session_id": ""},
]


class IdentityAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self, identities=None):
        self.requests = []
        self.bind_results = []
        self.identities = identities or [{"session_id": "opaque-session"}]

    async def start(self, request):
        self.requests.append(request)
        identity = self.identities[min(len(self.requests) - 1, len(self.identities) - 1)]
        self.bind_results.append(await request.bind_native_identity(identity))
        return object()

    async def submit(self, handle, request, emit):
        await emit({"type": "delta", "data": {"text": "answer"}})
        return AdapterResult(result_text="answer")

    async def cancel(self, handle, request):
        return None


def _identity_like_facts():
    return {
        "exact": _IDENTITY,
        "json": '{\n  "session_id": "opaque-session"\n}',
        "boundary": "prefix opaque-session suffix",
        "substring": "opaque-sessionish",
        "single": "a",
        "boolean": True,
        "number": 7,
        "keys": {
            "<redacted>": "existing",
            "opaque-session": "identity",
            "opaque-sessionish": "substring",
        },
    }


def _expected_trace_payload():
    return {
        "exact": _IDENTITY,
        "json": '{\n  "session_id": "opaque-session"\n}',
        "boundary": "prefix opaque-session suffix",
        "substring": "opaque-sessionish",
        "single": "a",
        "boolean": True,
        "number": 7,
        "keys": {
            "<redacted>": "existing",
            "opaque-session": "identity",
            "opaque-sessionish": "substring",
        },
    }


def _expected_fresh_delta():
    return {
        "exact": {"kind": "answer"},
        "json": '{"kind": "answer"}',
        "substring": "ordinary-text",
        "boolean": True,
        "number": 7,
        "keys": {"<redacted>": "existing", "ordinary": "fact"},
    }


def _single_character_payload():
    return {
        "exact": "a",
        "boundary": "prefix a suffix",
        "substring": "data",
        "boolean": True,
        "number": 7,
        "keys": {"a": "existing", "alpha": "unchanged"},
    }


class FactsAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self, fail=False, identity=_IDENTITY, payload=None, result_text="prefix opaque-session suffix"):
        self.fail = fail
        self.identity = identity
        self.payload = payload or _identity_like_facts()
        self.result_text = result_text

    async def start(self, request):
        await request.bind_native_identity(self.identity)
        return object()

    async def submit(self, handle, request, emit):
        await emit({"type": "delta", "data": self.payload})
        if self.fail:
            raise RuntimeError(self.result_text)
        return AdapterResult(result_text=self.result_text)

    async def cancel(self, handle, request):
        return None


class LateBindingAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self, identity):
        self.identity = identity

    async def start(self, request):
        return object()

    async def submit(self, handle, request, emit):
        await emit({"type": "delta", "data": {"text": "before-bind"}})
        await request.bind_native_identity(self.identity)
        return AdapterResult(result_text="after-bind")

    async def cancel(self, handle, request):
        return None


class CaughtRejectedBindingAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self, raise_after=False):
        self.calls = []
        self.bind_errors = []
        self.post_bind_identity = None
        self.raise_after = raise_after

    async def start(self, request):
        self.calls.append(("start", request.native_identity))
        return object()

    async def submit(self, handle, request, emit):
        self.calls.append(("submit", request.native_identity))
        for identity in ({"private_key": "bad-native"}, _IDENTITY):
            try:
                await request.bind_native_identity(identity)
            except ValueError as error:
                self.bind_errors.append(str(error))
        self.post_bind_identity = request.native_identity
        await emit({"type": "delta", "data": {"private_key": "bad-native"}})
        if self.raise_after:
            raise RuntimeError("private_key=bad-native")
        return AdapterResult(result_text="done")

    async def cancel(self, handle, request):
        return None


class RejectedParentWithChildAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.child_started = asyncio.Event()
        self.rejection_attempted = asyncio.Event()
        self.release = asyncio.Event()

    async def start(self, request):
        return object()

    async def submit(self, handle, request, emit):
        if request.message_id == "parent":
            await self.child_started.wait()
            self.rejection_attempted.set()
            await request.bind_native_identity({"private_key": "bad-native"})
        else:
            self.child_started.set()
        await self.release.wait()
        result_text = "child text" if request.message_id == "child" else "parent text"
        await emit({"type": "delta", "data": {"text": result_text}})
        return AdapterResult(result_text=result_text)

    async def cancel(self, handle, request):
        self.release.set()


class StreamingAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.before = {key: asyncio.Event() for key in ("first", "second")}
        self.release = {key: asyncio.Event() for key in ("first", "second")}

    async def start(self, request):
        return object()

    async def submit(self, handle, request, emit):
        message_id = request.message_id
        await emit({"type": "delta", "data": {"step": "before"}})
        self.before[message_id].set()
        await self.release[message_id].wait()
        await emit({"type": "delta", "data": {"step": "after"}})
        return AdapterResult(result_text=message_id)

    async def cancel(self, handle, request):
        self.release[request.message_id].set()


class EffectiveRequestAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.before_bind = []
        self.after_bind = []
        self.submit_identity = None
        self.cancel_identity = None
        self.submit_started = asyncio.Event()
        self.release = asyncio.Event()

    async def start(self, request):
        self.before_bind.append(request.native_identity)
        self.after_bind.append(await request.bind_native_identity(_IDENTITY))
        self.after_bind.append(request.native_identity)
        return object()

    async def submit(self, handle, request, emit):
        self.submit_identity = request.native_identity
        self.submit_started.set()
        await self.release.wait()
        return AdapterResult(result_text="done")

    async def cancel(self, handle, request):
        self.cancel_identity = request.native_identity
        self.release.set()


class ConcurrentIdentityAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.started = 0
        self.bind_results = []
        self.submit_identities = []
        self.ready = asyncio.Event()
        self.release = asyncio.Event()

    async def start(self, request):
        self.started += 1
        if self.started == 2:
            self.ready.set()
        await self.release.wait()
        self.bind_results.append(await request.bind_native_identity(_IDENTITY))
        return object()

    async def submit(self, handle, request, emit):
        self.submit_identities.append(request.native_identity)
        return AdapterResult(result_text="done")

    async def cancel(self, handle, request):
        return None


async def _submit_events(runtime, run_id, message_id):
    turn = await runtime.submit(run_id, {"id": message_id, "content": message_id})
    return turn, await _events(runtime, turn["id"])


async def _invalid_identity_events(runtime, run_id):
    events = []
    for index in range(len(_INVALID_IDENTITIES)):
        _, values = await _submit_events(runtime, run_id, f"invalid-{index}")
        events.extend(values)
    return events


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


async def _turn_events(runtime, run_id, message_id, content):
    turn = await runtime.submit(run_id, {"id": message_id, "content": content})
    return await _events(runtime, turn["id"])


async def _stream(runtime, run_id, message_id):
    turn = await runtime.submit(run_id, {"id": message_id, "content": message_id})
    return runtime.subscribe(turn["id"])


async def _next_event(stream):
    return await asyncio.wait_for(anext(stream), 1)


async def _rejected_parent_setup(tmp_path):
    adapter = RejectedParentWithChildAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    parent = await runtime.launch({"adapter": "fake"})
    parent_turn = await runtime.submit(parent["id"], {"id": "parent", "content": "delegate"})
    child = await runtime.delegate(parent["id"], {"adapter": "fake"}, parent_turn_id=parent_turn["id"])
    child_turn = await runtime.submit(child["id"], {"id": "child", "content": "task"})
    await adapter.rejection_attempted.wait()
    return adapter, runtime, parent_turn, child_turn


def _assert_rejected_parent_events(parent_events, child_events):
    assert [event["type"] for event in parent_events] == ["turn_start", "turn_end"]
    assert parent_events[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "runtime store native identity has unsupported shape",
    }
    assert child_events[-1]["data"] == {
        "status": "completed",
        "result_text": "child text",
    }
    assert not any(
        marker in json.dumps(parent_events)
        for marker in ("child_result", "private_key", "bad-native", "child text")
    )


@pytest.mark.asyncio
async def test_native_identity_binding_is_internal_to_runtime(tmp_path):
    adapter = IdentityAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"}, session_id="s-one")
    first = await _turn_events(runtime, run["id"], "m1", "opaque-session")
    second = await _turn_events(runtime, run["id"], "m2", "prefix opaque-session suffix")
    reopened = await runtime.launch({"adapter": "fake"}, session_id="s-one")

    assert "native_identity" not in run
    assert "native_identity" not in reopened
    assert first[0]["data"]["input"] == "opaque-session"
    assert second[0]["data"]["input"] == "prefix opaque-session suffix"
    assert first[-1]["data"]["result_text"] == "answer"
    assert adapter.requests[0].native_identity == _IDENTITY
    assert adapter.bind_results == [{"session_id": "opaque-session"}] * 2


@pytest.mark.asyncio
async def test_native_identity_binding_is_idempotent_for_repeated_turns(tmp_path):
    adapter = IdentityAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    first = await runtime.submit(run["id"], {"id": "m1", "content": "one"})
    await _events(runtime, first["id"])
    second = await runtime.submit(run["id"], {"id": "m2", "content": "two"})
    await _events(runtime, second["id"])

    assert [request.native_identity for request in adapter.requests] == [_IDENTITY, _IDENTITY]
    assert adapter.bind_results == [
        {"session_id": "opaque-session"},
        {"session_id": "opaque-session"},
    ]


@pytest.mark.asyncio
async def test_native_identity_binding_is_atomic_for_concurrent_turns(tmp_path):
    adapter = ConcurrentIdentityAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    turns = await asyncio.gather(
        runtime.submit(run["id"], {"id": "m1", "content": "one"}),
        runtime.submit(run["id"], {"id": "m2", "content": "two"}),
    )
    await adapter.ready.wait()
    adapter.release.set()
    events = await asyncio.gather(*(_events(runtime, turn["id"]) for turn in turns))

    assert adapter.bind_results == [_IDENTITY, _IDENTITY]
    assert adapter.submit_identities == [_IDENTITY, _IDENTITY]
    assert all(trace[-1]["data"]["status"] == "completed" for trace in events)


@pytest.mark.asyncio
@pytest.mark.parametrize("fail", [False, True], ids=["result", "error"])
async def test_native_identity_does_not_rewrite_trace_facts(tmp_path, fail):
    adapter = FactsAdapter(fail)
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "redaction")

    assert events[1]["data"] == _expected_trace_payload()
    terminal = events[-1]["data"]
    assert terminal["result_text"] == (None if fail else "prefix opaque-session suffix")
    assert terminal.get("error") == ("prefix opaque-session suffix" if fail else None)
    public = await runtime.submit(run["id"], {"id": "redaction", "content": "redaction"})
    assert "native_identity" not in public


@pytest.mark.asyncio
async def test_single_character_identity_does_not_rewrite_facts(tmp_path):
    adapter = FactsAdapter(identity=_ONE_CHARACTER_IDENTITY, payload=_single_character_payload(), result_text="a")
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "single-character")

    assert events[1]["data"] == _single_character_payload()
    assert events[-1]["data"]["result_text"] == "a"


@pytest.mark.asyncio
async def test_first_binding_updates_submit_and_cancel_requests(tmp_path):
    adapter = EffectiveRequestAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    turn = await runtime.submit(run["id"], {"id": "cancel", "content": "cancel"})
    await adapter.submit_started.wait()

    await runtime.cancel(turn["id"])

    assert adapter.before_bind == [None]
    assert adapter.after_bind == [_IDENTITY, _IDENTITY]
    assert adapter.submit_identity == _IDENTITY
    assert adapter.cancel_identity == _IDENTITY


@pytest.mark.asyncio
async def test_late_binding_preserves_prebinding_events(tmp_path):
    adapter = LateBindingAdapter(_IDENTITY)
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "late")

    assert events[1]["data"] == {"text": "before-bind"}
    assert events[-1]["data"] == {
        "status": "completed",
        "result_text": "after-bind",
    }


@pytest.mark.asyncio
async def test_rejected_binding_is_terminal_when_adapter_catches(tmp_path):
    adapter = CaughtRejectedBindingAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "rejected-late")

    assert [event["type"] for event in events] == ["turn_start", "turn_end"]
    assert events[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "runtime store native identity has unsupported shape",
    }
    assert adapter.calls == [("start", None), ("submit", None)]
    assert len(adapter.bind_errors) == 2
    assert adapter.post_bind_identity is None


@pytest.mark.asyncio
async def test_rejected_binding_hides_adapter_error_text(tmp_path):
    adapter = CaughtRejectedBindingAdapter(raise_after=True)
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "rejected-error")

    assert events[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "runtime store native identity has unsupported shape",
    }
    assert "bad-native" not in json.dumps(events)
    assert adapter.post_bind_identity is None


@pytest.mark.asyncio
async def test_rejected_parent_drops_late_child_result(tmp_path):
    adapter, runtime, parent_turn, child_turn = await _rejected_parent_setup(tmp_path)
    adapter.release.set()
    parent_events, child_events = await asyncio.gather(
        _events(runtime, parent_turn["id"]), _events(runtime, child_turn["id"])
    )
    _assert_rejected_parent_events(parent_events, child_events)


@pytest.mark.asyncio
async def test_never_bind_adapter_streams_each_turn_in_order(tmp_path):
    adapter = StreamingAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    first = await _stream(runtime, run["id"], "first")
    assert (await _next_event(first))["type"] == "turn_start"
    await adapter.before["first"].wait()
    assert (await _next_event(first))["data"]["step"] == "before"
    second = await _stream(runtime, run["id"], "second")
    assert (await _next_event(second))["type"] == "turn_start"
    await adapter.before["second"].wait()
    assert (await _next_event(second))["data"]["step"] == "before"
    adapter.release["second"].set()
    assert (await _next_event(second))["data"]["step"] == "after"
    assert (await _next_event(second))["type"] == "turn_end"
    adapter.release["first"].set()
    assert (await _next_event(first))["data"]["step"] == "after"
    assert (await _next_event(first))["type"] == "turn_end"


@pytest.mark.asyncio
async def test_conflicting_native_identity_binding_is_rejected_without_rebinding(tmp_path):
    adapter = IdentityAdapter([_IDENTITY, {"session_id": "other-session"}, _IDENTITY])
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    await _turn_events(runtime, run["id"], "m1", "one")
    conflict_events = await _turn_events(runtime, run["id"], "m2", "two")
    await _turn_events(runtime, run["id"], "m3", "three")

    assert conflict_events[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "runtime store native identity conflicts",
    }
    assert adapter.requests[2].native_identity == {"session_id": "opaque-session"}
    assert adapter.bind_results == [
        {"session_id": "opaque-session"},
        {"session_id": "opaque-session"},
    ]


_SEED_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request):
        await request.bind_native_identity({"session_id": "opaque-session"})
        return object()
    async def submit(self, handle, request, emit):
        return AdapterResult(result_text="seeded")
    async def cancel(self, handle, request): return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"adapter": "fake"}, session_id="s-one")
    turn = await runtime.submit(run["id"], {"id": "m1", "content": "seed"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps({"run_id": run["id"], "session_id": "s-one"}))

asyncio.run(main())
'''


_RECOVER_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request):
        self.calls.append(["start", request.native_identity])
        self.calls.append(["bound", await request.bind_native_identity({"session_id": "opaque-session"})])
        return object()
    async def submit(self, handle, request, emit):
        self.calls.append(["submit", request.native_identity])
        await emit({"type": "delta", "data": {
            "exact": {"kind": "answer"},
            "json": '{"kind": "answer"}',
            "substring": "ordinary-text",
            "boolean": True,
            "number": 7,
            "keys": {"<redacted>": "existing", "ordinary": "fact"},
        }})
        return AdapterResult(result_text="answer")
    async def cancel(self, handle, request): return None

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    before = list(adapter.calls)
    run = await runtime.launch({"adapter": "fake"}, session_id="s-one")
    turn = await runtime.submit(run["id"], {"id": "m2", "content": "recover"})
    events = [event async for event in runtime.subscribe(turn["id"])]
    public_turn = await runtime.submit(run["id"], {"id": "m2", "content": "recover"})
    public = {"run": run, "turn": public_turn, "events": events}
    print(json.dumps({"before": before, "calls": adapter.calls, "run_id": run["id"], "public": public}))

asyncio.run(main())
'''


def _run_process(script, root, *arguments):
    return subprocess.run([sys.executable, "-c", script, str(root), *arguments], cwd=_RUNTIME_ROOT, check=True, capture_output=True, text=True, timeout=5)


def _output(result):
    return json.loads(result.stdout)


def test_native_identity_is_restored_before_fresh_adapter_start(tmp_path):
    seeded = _output(_run_process(_SEED_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_PROCESS, tmp_path))

    assert recovered["before"] == []
    assert recovered["run_id"] == seeded["run_id"]
    assert recovered["calls"] == [
        ["start", _IDENTITY],
        ["bound", _IDENTITY],
        ["submit", _IDENTITY],
    ]
    assert recovered["public"]["events"][1]["data"] == _expected_fresh_delta()
    assert recovered["public"]["events"][-1]["data"] == {
        "status": "completed",
        "result_text": "answer",
    }
    assert '"opaque-session"' not in json.dumps(recovered["public"])


_REJECT_UNKNOWN_PROCESS = r'''
import json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "other"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start")
    async def submit(self, handle, request, emit): self.calls.append("submit")
    async def cancel(self, handle, request): self.calls.append("cancel")

root = Path(sys.argv[1])
adapter = Adapter()
try:
    Runtime(root, {"other": adapter})
except Exception as error:
    print(json.dumps({"error": type(error).__name__ + ":" + str(error), "calls": adapter.calls}))
else:
    print(json.dumps({"constructed": True, "calls": adapter.calls}))
'''


_CORRUPT_IDENTITY_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

root = Path(sys.argv[1])
connection = sqlite3.connect(root / "runs.sqlite3")
connection.execute("UPDATE runs SET native_identity = ?", (sys.argv[2],))
connection.commit()
connection.close()
'''


_REJECT_IDENTITY_PROCESS = r'''
import json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start")
    async def submit(self, handle, request, emit): self.calls.append("submit")
    async def cancel(self, handle, request): self.calls.append("cancel")

root = Path(sys.argv[1])
adapter = Adapter()
try:
    Runtime(root, {"fake": adapter})
except Exception as error:
    print(json.dumps({"error": type(error).__name__ + ":" + str(error), "calls": adapter.calls}))
else:
    print(json.dumps({"constructed": True, "calls": adapter.calls}))
'''


def test_unknown_adapter_is_rejected_before_fresh_recovery_calls(tmp_path):
    _run_process(_SEED_PROCESS, tmp_path)
    rejected = _output(_run_process(_REJECT_UNKNOWN_PROCESS, tmp_path))

    assert rejected["error"].startswith("ValueError:runtime adapter is unavailable: fake")
    assert rejected["calls"] == []


@pytest.mark.parametrize(
    "identity",
    ["{\"adapter_id\":\"fake\"}", "[]", "{\"adapter_id\":\"other\",\"value\":{\"session_id\":\"opaque-session\"}}"],
    ids=["malformed", "empty-payload", "wrong-owner"],
)
def test_invalid_native_identity_state_fails_closed_before_adapter_calls(tmp_path, identity):
    _run_process(_SEED_PROCESS, tmp_path)
    _run_process(_CORRUPT_IDENTITY_PROCESS, tmp_path, identity)
    rejected = _output(_run_process(_REJECT_IDENTITY_PROCESS, tmp_path))

    assert rejected["error"].startswith("RunStoreError:runtime store native identity")
    assert rejected["calls"] == []


@pytest.mark.asyncio
async def test_native_identity_accepts_only_the_identifier_schema(tmp_path):
    adapter = IdentityAdapter([*_INVALID_IDENTITIES, _IDENTITY])
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    rejected_events = await _invalid_identity_events(runtime, run["id"])
    _, accepted_events = await _submit_events(runtime, run["id"], "accepted")

    assert all(event["data"]["status"] == "error" for event in rejected_events if event["type"] == "turn_end")
    assert all("secret" not in json.dumps(events) for events in [rejected_events])
    assert accepted_events[-1]["data"] == {
        "status": "completed",
        "result_text": "answer",
    }
    assert adapter.bind_results == [_IDENTITY]

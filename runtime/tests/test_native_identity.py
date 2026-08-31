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
        await emit({"type": "delta", "data": {"text": "opaque-session"}})
        return AdapterResult(result_text="opaque-session")

    async def cancel(self, handle, request):
        return None


def _redaction_payload():
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


def _expected_redaction_payload():
    return {
        "exact": "<redacted>",
        "json": "<redacted>",
        "boundary": "prefix <redacted> suffix",
        "substring": "opaque-sessionish",
        "single": "a",
        "boolean": True,
        "number": 7,
        "keys": {
            "<redacted>": "existing",
            "<redacted>#2": "identity",
            "opaque-sessionish": "substring",
        },
    }


def _expected_fresh_delta():
    return {
        "exact": "<redacted>",
        "json": "<redacted>",
        "substring": "opaque-sessionish",
        "boolean": True,
        "number": 7,
        "keys": {"<redacted>": "existing", "<redacted>#2": "identity"},
    }


class RedactionAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self, fail=False):
        self.fail = fail

    async def start(self, request):
        await request.bind_native_identity(_IDENTITY)
        return object()

    async def submit(self, handle, request, emit):
        await emit({"type": "delta", "data": _redaction_payload()})
        if self.fail:
            raise RuntimeError("prefix opaque-session suffix")
        return AdapterResult(result_text="prefix opaque-session suffix")

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
        await emit({"type": "delta", "data": {"text": "opaque-session"}})
        await request.bind_native_identity(self.identity)
        return AdapterResult(result_text="opaque-session")

    async def cancel(self, handle, request):
        return None


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


@pytest.mark.asyncio
async def test_native_identity_binding_is_internal_to_runtime(tmp_path):
    adapter = IdentityAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"}, session_id="s-one")
    turn = await runtime.submit(run["id"], {"id": "m1", "content": "hello"})
    trace = await _events(runtime, turn["id"])
    reopened = await runtime.launch({"adapter": "fake"}, session_id="s-one")

    assert "native_identity" not in run
    assert "native_identity" not in reopened
    assert "opaque-session" not in json.dumps(trace)
    assert trace[-1]["data"]["result_text"] == "<redacted>"
    assert adapter.requests[0].native_identity == _IDENTITY
    assert adapter.bind_results == [{"session_id": "opaque-session"}]


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
async def test_native_identity_redaction_preserves_trace_facts(tmp_path, fail):
    adapter = RedactionAdapter(fail)
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "redaction")

    assert events[1]["data"] == _expected_redaction_payload()
    terminal = events[-1]["data"]
    assert terminal["result_text"] == (None if fail else "prefix <redacted> suffix")
    assert terminal.get("error") == ("prefix <redacted> suffix" if fail else None)
    public = await runtime.submit(run["id"], {"id": "redaction", "content": "redaction"})
    assert "native_identity" not in public
    assert '"opaque-session"' not in json.dumps(events + [public])


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
async def test_late_binding_redacts_prebinding_events(tmp_path):
    adapter = LateBindingAdapter(_IDENTITY)
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "late")

    assert events[1]["data"] == {"text": "<redacted>"}
    assert events[-1]["data"] == {
        "status": "completed",
        "result_text": "<redacted>",
    }


@pytest.mark.asyncio
async def test_rejected_late_binding_discards_prebinding_events(tmp_path):
    adapter = LateBindingAdapter({"private_key": "bad-native"})
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    _, events = await _submit_events(runtime, run["id"], "rejected-late")

    assert [event["type"] for event in events] == ["turn_start", "turn_end"]
    assert "bad-native" not in json.dumps(events)


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
            "exact": {"session_id": "opaque-session"},
            "json": '{"session_id": "opaque-session"}',
            "substring": "opaque-sessionish",
            "boolean": True,
            "number": 7,
            "keys": {"<redacted>": "existing", "opaque-session": "identity"},
        }})
        return AdapterResult(result_text="opaque-session")
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
        "result_text": "<redacted>",
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
        "result_text": "<redacted>",
    }
    assert adapter.bind_results == [_IDENTITY]

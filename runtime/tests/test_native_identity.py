import json
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


_RUNTIME_ROOT = Path(__file__).parents[1]
_IDENTITY = {"session_id": "opaque-session"}


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
    assert adapter.requests[0].native_identity is None
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

    assert [request.native_identity for request in adapter.requests] == [
        None,
        {"session_id": "opaque-session"},
    ]
    assert adapter.bind_results == [
        {"session_id": "opaque-session"},
        {"session_id": "opaque-session"},
    ]


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
        return AdapterResult(result_text="recovered")
    async def cancel(self, handle, request): return None

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    before = list(adapter.calls)
    run = await runtime.launch({"adapter": "fake"}, session_id="s-one")
    turn = await runtime.submit(run["id"], {"id": "m2", "content": "recover"})
    events = [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps({"before": before, "calls": adapter.calls, "run_id": run["id"], "events": events}))

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
    assert recovered["events"][-1]["data"] == {"status": "completed", "result_text": "recovered"}


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
before = (root / "runs.sqlite3").read_bytes()
adapter = Adapter()
try:
    Runtime(root, {"other": adapter})
except Exception as error:
    print(json.dumps({"error": type(error).__name__ + ":" + str(error), "calls": adapter.calls, "unchanged": (root / "runs.sqlite3").read_bytes() == before}))
else:
    print(json.dumps({"constructed": True, "calls": adapter.calls, "unchanged": (root / "runs.sqlite3").read_bytes() == before}))
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
before = (root / "runs.sqlite3").read_bytes()
adapter = Adapter()
try:
    Runtime(root, {"fake": adapter})
except Exception as error:
    print(json.dumps({"error": type(error).__name__ + ":" + str(error), "calls": adapter.calls, "unchanged": (root / "runs.sqlite3").read_bytes() == before}))
else:
    print(json.dumps({"constructed": True, "calls": adapter.calls, "unchanged": (root / "runs.sqlite3").read_bytes() == before}))
'''


def test_unknown_adapter_is_rejected_before_fresh_recovery_calls(tmp_path):
    _run_process(_SEED_PROCESS, tmp_path)
    rejected = _output(_run_process(_REJECT_UNKNOWN_PROCESS, tmp_path))

    assert rejected["error"].startswith("ValueError:runtime adapter is unavailable: fake")
    assert rejected["calls"] == []
    assert rejected["unchanged"]


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
    assert rejected["unchanged"]


@pytest.mark.asyncio
async def test_native_identity_credentials_are_rejected_and_not_persisted(tmp_path):
    adapter = IdentityAdapter([{"api_key": "secret"}, _IDENTITY])
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"})
    rejected = await runtime.submit(run["id"], {"id": "m1", "content": "hello"})
    rejected_events = await _events(runtime, rejected["id"])
    accepted = await runtime.submit(run["id"], {"id": "m2", "content": "next"})
    await _events(runtime, accepted["id"])

    assert rejected_events[-1]["data"] == {
        "status": "error",
        "result_text": None,
        "error": "runtime store native identity contains credentials",
    }
    assert "secret" not in json.dumps(rejected_events)
    assert adapter.requests[1].native_identity is None

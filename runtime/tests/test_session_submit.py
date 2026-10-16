import json
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


SPEC = {"id": "main", "adapter": "fake"}
RUNTIME_ROOT = Path(__file__).parents[1]


_CREATE_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return AdapterResult(result_text="answer")
    async def cancel(self, handle, request): return None

    async def close(self): return None

async def main():
    session_id = sys.argv[2]
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    await runtime.launch({"id": "main", "adapter": "fake"}, session_id=session_id)
    turn = await runtime.submit(session_id, {"id": "message-1", "content": "one"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps(await runtime.submit(session_id, {"id": "message-1", "content": "changed"})))

asyncio.run(main())
'''


_RESTORE_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start"); return object()
    async def submit(self, handle, request, emit): self.calls.append("submit"); return AdapterResult(result_text="new")
    async def cancel(self, handle, request): self.calls.append("cancel")

    async def close(self): return None

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    turn = await runtime.submit(sys.argv[2], {"id": "message-1", "content": "changed again"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps({"turn": turn, "calls": adapter.calls}))

asyncio.run(main())
'''


class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.calls = []

    async def start(self, request):
        self.calls.append(("start", request.message_id))
        return object()

    async def submit(self, handle, request, emit):
        self.calls.append(("submit", request.message_id))
        return AdapterResult(result_text=request.input)

    async def cancel(self, handle, request):
        self.calls.append(("cancel", request.message_id))

    async def close(self):
        return None


async def events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


def run_process(tmp_path, script, session_id):
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), session_id],
        cwd=RUNTIME_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


@pytest.mark.asyncio
async def test_submit_resolves_session_bound_root_run(tmp_path):
    adapter = Adapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch(SPEC, session_id="session-201")

    turn = await runtime.submit("session-201", {"id": "message-1", "content": "one"})
    observed = await events(runtime, turn["id"])

    assert turn["run_id"] == run["id"]
    assert observed[-1]["data"] == {"status": "completed", "result_text": "one"}
    assert adapter.calls == [("start", "message-1"), ("submit", "message-1")]


@pytest.mark.asyncio
async def test_same_message_reuses_turn_and_different_message_creates_turn(tmp_path):
    adapter = Adapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    await runtime.launch(SPEC, session_id="session-201")
    first = await runtime.submit("session-201", {"id": "message-1", "content": "one"})
    duplicate = await runtime.submit("session-201", {"id": "message-1", "content": "changed"})
    second = await runtime.submit("session-201", {"id": "message-2", "content": "two"})
    await events(runtime, first["id"])
    await events(runtime, second["id"])
    assert duplicate["id"] == first["id"]
    assert second["id"] != first["id"]
    completed_duplicate = await runtime.submit(
        "session-201", {"id": "message-1", "content": "changed again"}
    )
    assert completed_duplicate["id"] == first["id"]
    assert completed_duplicate["status"] == "completed"
    assert adapter.calls == [("start", "message-1"), ("submit", "message-1"), ("start", "message-2"), ("submit", "message-2")]


@pytest.mark.asyncio
async def test_unbound_session_rejects_before_adapter_or_trace(tmp_path):
    adapter = Adapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    await runtime.launch(SPEC)
    with pytest.raises(KeyError, match="session not found"):
        await runtime.submit("session-unbound", {"id": "message-1", "content": "one"})
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_run_identity_is_not_a_session_target(tmp_path):
    adapter = Adapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch(SPEC, session_id="session-201")
    with pytest.raises(KeyError, match="session not found"):
        await runtime.submit(run["id"], {"id": "message-1", "content": "one"})
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_submit_reuses_turn_after_fresh_interpreter(tmp_path):
    original = run_process(tmp_path, _CREATE_PROCESS, "session-201")
    recovered = run_process(tmp_path, _RESTORE_PROCESS, "session-201")
    assert recovered["turn"] == original
    assert recovered["calls"] == []

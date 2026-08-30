import json
import subprocess
import sys
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).parents[1]


_COMPLETED_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.requests = []
    async def start(self, request):
        self.requests.append(request)
        return object()
    async def submit(self, handle, request, emit):
        await emit({"type": "delta", "data": {"text": request.input}})
        return AdapterResult(result_text="answer:" + request.input)
    async def cancel(self, handle, request):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake", "params": {"mode": "frozen"}})
    first = await runtime.submit(run["id"], {"id": "m1", "content": "one"})
    first_events = await collect(runtime, first["id"])
    second = await runtime.submit(run["id"], {"id": "m2", "content": "two"})
    second_events = await collect(runtime, second["id"])
    print(json.dumps({"run_id": run["id"], "turn_id": second["id"], "events": second_events, "first": first_events}))

asyncio.run(main())
'''


_RECOVER_COMPLETED_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    supports_multiple_writers = True
    def __init__(self, adapter_id):
        self.adapter_id = adapter_id
        self.calls = []
        self.requests = []
    async def start(self, request):
        self.calls.append(["start", self.adapter_id, request.message_id])
        self.requests.append(request)
        return object()
    async def submit(self, handle, request, emit):
        self.calls.append(["submit", self.adapter_id, request.message_id])
        await emit({"type": "delta", "data": {"text": request.input}})
        return AdapterResult(result_text="answer:" + request.input)
    async def cancel(self, handle, request):
        self.calls.append(["cancel", self.adapter_id, request.message_id])

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter("fake")
    runtime = Runtime(Path(sys.argv[1]), {"other": Adapter("other"), "fake": adapter})
    before = list(adapter.calls)
    duplicate = await runtime.submit(sys.argv[2], {"id": "m2", "content": "changed"})
    replay = await collect(runtime, sys.argv[3])
    restored = await runtime.submit(sys.argv[2], {"id": "m3", "content": "three"})
    events = await collect(runtime, restored["id"])
    request = adapter.requests[0]
    print(json.dumps({"before": before, "duplicate": duplicate, "replay": replay, "events": events, "context": list(request.context), "adapter": request.agent_snapshot["adapter"], "calls": adapter.calls}))

asyncio.run(main())
'''


_REVERSE_CONTEXT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.gates = {"m1": asyncio.Event(), "m2": asyncio.Event()}
    async def start(self, request):
        return object()
    async def submit(self, handle, request, emit):
        await self.gates[request.message_id].wait()
        return AdapterResult(result_text="answer:" + request.message_id)
    async def cancel(self, handle, request):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"})
    first = await runtime.submit(run["id"], {"id": "m1", "content": "one"})
    second = await runtime.submit(run["id"], {"id": "m2", "content": "two"})
    adapter.gates["m2"].set()
    await collect(runtime, second["id"])
    adapter.gates["m1"].set()
    await collect(runtime, first["id"])
    print(run["id"])

asyncio.run(main())
'''


_RECOVER_CONTEXT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.requests = []
    async def start(self, request):
        self.requests.append(request)
        return object()
    async def submit(self, handle, request, emit):
        return AdapterResult(result_text="answer:m3")
    async def cancel(self, handle, request):
        return None

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    turn = await runtime.submit(sys.argv[2], {"id": "m3", "content": "three"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps(list(adapter.requests[0].context)))

asyncio.run(main())
'''


_CRASH_PROCESS = r'''
import asyncio, json, os, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.calls = []
    async def start(self, request):
        self.calls.append(["start", request.message_id])
        return object()
    async def submit(self, handle, request, emit):
        self.calls.append(["submit", request.message_id])
        await asyncio.Event().wait()
    async def cancel(self, handle, request):
        self.calls.append(["cancel", request.message_id])

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    parent = await runtime.launch({"id": "main", "adapter": "fake"})
    parent_turn = await runtime.submit(parent["id"], {"id": "parent", "content": "delegate"})
    child = await runtime.delegate(parent["id"], {"id": "child", "adapter": "fake"}, parent_turn_id=parent_turn["id"])
    child_turn = await runtime.submit(child["id"], {"id": "child", "content": "work"})
    await asyncio.sleep(0.1)
    print(json.dumps({"parent_run": parent["id"], "parent_turn": parent_turn["id"], "child_run": child["id"], "child_turn": child_turn["id"]}), flush=True)
    os._exit(0)

asyncio.run(main())
'''


_RECOVER_CRASH_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.calls = []
    async def start(self, request):
        self.calls.append(["start", request.message_id])
        return object()
    async def submit(self, handle, request, emit):
        self.calls.append(["submit", request.message_id])
        await emit({"type": "delta", "data": {"text": request.input}})
        return AdapterResult(result_text="resumed")
    async def cancel(self, handle, request):
        self.calls.append(["cancel", request.message_id])

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    before = list(adapter.calls)
    child = await collect(runtime, sys.argv[2])
    parent = await collect(runtime, sys.argv[3])
    duplicate = await runtime.submit(sys.argv[4], {"id": "child", "content": "changed"})
    resumed = await runtime.submit(sys.argv[5], {"id": "new", "content": "resume"})
    resumed_events = await collect(runtime, resumed["id"])
    print(json.dumps({"before": before, "child": child, "parent": parent, "duplicate": duplicate, "resumed": resumed_events, "calls": adapter.calls}))

asyncio.run(main())
'''


_NESTED_CRASH_PROCESS = r'''
import asyncio, json, os, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request):
        return object()
    async def submit(self, handle, request, emit):
        await asyncio.Event().wait()
    async def cancel(self, handle, request):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    while True:
        main_run = await runtime.launch({"id": "main", "adapter": "fake"})
        main_turn = await runtime.submit(main_run["id"], {"id": "main", "content": "main"})
        child_run = await runtime.delegate(main_run["id"], {"id": "child", "adapter": "fake"}, parent_turn_id=main_turn["id"])
        child_turn = await runtime.submit(child_run["id"], {"id": "child", "content": "child"})
        grandchild_run = await runtime.delegate(child_run["id"], {"id": "grandchild", "adapter": "fake"}, parent_turn_id=child_turn["id"])
        grandchild_turn = await runtime.submit(grandchild_run["id"], {"id": "grandchild", "content": "grandchild"})
        chain = {"main_turn": main_turn["id"], "child_turn": child_turn["id"], "grandchild_turn": grandchild_turn["id"], "child_run": child_run["id"], "grandchild_run": grandchild_run["id"]}
        if child_run["id"] < grandchild_run["id"]:
            await asyncio.sleep(0.1)
            print(json.dumps(chain), flush=True)
            os._exit(0)

asyncio.run(main())
'''


_RECOVER_NESTED_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self):
        self.calls = []
    async def start(self, request):
        self.calls.append(["start", request.message_id])
        return object()
    async def submit(self, handle, request, emit):
        self.calls.append(["submit", request.message_id])
        await asyncio.Event().wait()
    async def cancel(self, handle, request):
        self.calls.append(["cancel", request.message_id])

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    chain = json.loads(sys.argv[2])
    streams = [await collect(runtime, chain[key]) for key in ("grandchild_turn", "child_turn", "main_turn")]
    order = [[event["turn_id"], event["type"]] for stream in streams for event in stream if event["type"] in {"child_result", "turn_end"}]
    print(json.dumps({"order": order, "calls": adapter.calls}))

asyncio.run(main())
'''


_CORRUPT_STORE_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.executescript("""
CREATE TABLE metadata (key TEXT, value TEXT);
CREATE TABLE runs (id TEXT, agent_snapshot TEXT, adapter_id TEXT, parent_run_id TEXT, completed_context TEXT);
CREATE TABLE turns (id TEXT, run_id TEXT, message_id TEXT, input TEXT, context TEXT, submit_seq INTEGER, status TEXT, result_text TEXT, error TEXT);
CREATE TABLE delegations (child_run_id TEXT, parent_run_id TEXT, parent_turn_id TEXT);
CREATE TABLE message_index (run_id TEXT, message_id TEXT, turn_id TEXT);
CREATE TABLE events (turn_id TEXT, seq INTEGER, run_id TEXT, type TEXT, time TEXT, data TEXT);
INSERT INTO metadata VALUES ('format', 'runtime-run-store'), ('version', '1');
INSERT INTO runs VALUES ('r-main', '{"adapter":"fake"}', 'fake', NULL, '[]');
INSERT INTO turns VALUES
    ('t-one', 'r-main', 'm-one', '"one"', '[]', 0, 'running', NULL, NULL),
    ('t-two', 'r-main', 'm-two', '"two"', '[]', 0, 'running', NULL, NULL);
INSERT INTO message_index VALUES ('r-main', 'm-one', 't-one'), ('r-main', 'm-two', 't-two');
INSERT INTO events VALUES
    ('t-one', 0, 'r-main', 'turn_start', 'time', '{"message_id":"m-one","input":"one"}'),
    ('t-two', 0, 'r-main', 'turn_start', 'time', '{"message_id":"m-two","input":"two"}');
""")
connection.close()
'''


_FAIL_STARTUP_PROCESS = r'''
from pathlib import Path
import sys
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request):
        return object()
    async def submit(self, handle, request, emit):
        return None
    async def cancel(self, handle, request):
        return None

try:
    Runtime(Path(sys.argv[1]), {"fake": Adapter()})
except Exception as error:
    print(type(error).__name__ + ":" + str(error))
'''


def _run_process(script, root, *arguments):
    command = [sys.executable, "-c", script, str(root), *arguments]
    return subprocess.run(command, cwd=_RUNTIME_ROOT, check=True, capture_output=True, text=True, timeout=5)


def _output(result):
    return json.loads(result.stdout)


def test_completed_run_recovers_in_a_fresh_interpreter(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_COMPLETED_PROCESS, tmp_path, created["run_id"], created["turn_id"]))
    assert recovered["before"] == []
    assert recovered["duplicate"]["id"] == created["turn_id"]
    assert recovered["replay"] == created["events"]
    assert recovered["context"] == [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:one"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:two"}]
    assert recovered["adapter"] == "fake"
    assert recovered["calls"] == [["start", "fake", "m3"], ["submit", "fake", "m3"]]


def test_recovered_context_keeps_submit_order_after_reverse_completion(tmp_path):
    run_id = _run_process(_REVERSE_CONTEXT_PROCESS, tmp_path).stdout.strip()
    result = _run_process(_RECOVER_CONTEXT_PROCESS, tmp_path, run_id)
    assert json.loads(result.stdout) == [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:m1"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:m2"}]


def test_restart_terminalizes_children_before_parent_in_a_fresh_interpreter(tmp_path):
    created = _output(_run_process(_CRASH_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_CRASH_PROCESS, tmp_path, created["child_turn"], created["parent_turn"], created["child_run"], created["parent_run"]))
    expected = {"status": "error", "result_text": None, "error": "runtime restarted before turn completion"}
    assert recovered["before"] == []
    assert [event["type"] for event in recovered["child"]] == ["turn_start", "turn_end"]
    assert [event["type"] for event in recovered["parent"]] == ["turn_start", "child_result", "turn_end"]
    assert recovered["child"][-1]["type"] == "turn_end" and recovered["child"][-1]["data"] == expected
    assert recovered["parent"][1]["type"] == "child_result" and recovered["parent"][1]["data"] == {"child_run_id": created["child_run"], "child_turn_id": created["child_turn"], **expected}
    assert recovered["parent"][-1]["data"] == expected
    assert recovered["duplicate"]["status"] == "error"
    assert recovered["resumed"][-1]["data"]["status"] == "completed"
    assert recovered["calls"] == [["start", "new"], ["submit", "new"]]


def test_nested_recovery_unwinds_grandchild_before_parent_in_fresh_interpreter(tmp_path):
    created = _output(_run_process(_NESTED_CRASH_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_NESTED_PROCESS, tmp_path, json.dumps(created)))
    assert recovered["order"] == [
        [created["grandchild_turn"], "turn_end"],
        [created["child_turn"], "child_result"],
        [created["child_turn"], "turn_end"],
        [created["main_turn"], "child_result"],
        [created["main_turn"], "turn_end"],
    ]
    assert recovered["calls"] == []


def test_same_shape_store_with_missing_constraints_rejects_duplicate_submit_seq(tmp_path):
    _run_process(_CORRUPT_STORE_PROCESS, tmp_path)
    result = _run_process(_FAIL_STARTUP_PROCESS, tmp_path)
    assert result.stdout.startswith("RunStoreError:runtime store")


def test_missing_adapter_fails_startup_without_fallback(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    script = """
from pathlib import Path
import sys
from runtime.runtime import Runtime
class Adapter:
    adapter_id = "other"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return None
    async def cancel(self, handle, request): return None
try:
    Runtime(Path(sys.argv[1]), {"other": Adapter()})
except ValueError as error:
    print(error)
"""
    result = _run_process(script, tmp_path, created["run_id"])
    assert result.stdout.strip() == "runtime adapter is unavailable: fake"


def test_corrupt_runtime_store_fails_clearly(tmp_path):
    (tmp_path / "runs.sqlite3").write_bytes(b"not a sqlite database")
    script = """
from pathlib import Path
import sys
from runtime.runtime import Runtime
try:
    Runtime(Path(sys.argv[1]), {})
except Exception as error:
    print(type(error).__name__ + ":" + str(error))
"""
    result = _run_process(script, tmp_path)
    assert result.stdout.startswith("RunStoreError:runtime store")


def test_existing_non_runtime_state_does_not_trigger_fallback(tmp_path):
    (tmp_path / "traces").mkdir()
    script = """
from pathlib import Path
import sys
from runtime.runtime import Runtime
try:
    Runtime(Path(sys.argv[1]), {})
except Exception as error:
    print(type(error).__name__ + ":" + str(error))
"""
    result = _run_process(script, tmp_path)
    assert result.stdout.strip() == "RunStoreError:runtime store is missing or incomplete"

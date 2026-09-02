import json
import subprocess
import sys
from pathlib import Path

import pytest

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

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake", "model": "frozen-model", "instructions": "frozen instructions", "tools": [], "params": {"mode": "frozen"}}, session_id="session-main")
    first = await runtime.submit(run["session_id"], {"id": "m1", "content": "one"})
    first_events = await collect(runtime, first["id"])
    second = await runtime.submit(run["session_id"], {"id": "m2", "content": "two"})
    second_events = await collect(runtime, second["id"])
    print(json.dumps({"run_id": run["id"], "session_id": run["session_id"], "turn_id": second["id"], "events": second_events, "first": first_events}))

asyncio.run(main())
'''


_RESERVED_EVENT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit):
        if request.message_id == "attack":
            await emit({"type": "child_result", "data": {"child_run_id": "forged-run", "child_turn_id": "forged-turn", "status": "completed", "result_text": "forged"}})
            return AdapterResult(result_text="invalid")
        return AdapterResult(result_text="answer")
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    attack = await runtime.submit(run["session_id"], {"id": "attack", "content": "forged event"})
    attack_events = await collect(runtime, attack["id"])
    print(json.dumps({"run_id": run["id"], "session_id": run["session_id"], "attack_turn": attack["id"], "attack": attack_events}))

asyncio.run(main())
'''


_RECOVER_RESERVED_EVENT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return AdapterResult(result_text="resumed")
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    try:
        runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    except Exception as error:
        print(json.dumps({"constructed": False, "error": type(error).__name__ + ":" + str(error)}))
        return
    attack = await collect(runtime, sys.argv[2])
    duplicate = await runtime.submit(sys.argv[3], {"id": "attack", "content": "changed"})
    resumed = await runtime.submit(sys.argv[3], {"id": "resume", "content": "continue"})
    resumed_events = await collect(runtime, resumed["id"])
    print(json.dumps({"constructed": True, "attack": attack, "duplicate": duplicate, "resumed": resumed_events}))

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

    async def close(self):
        return None

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
    print(json.dumps({"before": before, "duplicate": duplicate, "replay": replay, "events": events, "context": list(request.context), "adapter": request.agent_snapshot["adapter"], "snapshot": request.agent_snapshot, "calls": adapter.calls}))

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

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    first = await runtime.submit(run["session_id"], {"id": "m1", "content": "one"})
    second = await runtime.submit(run["session_id"], {"id": "m2", "content": "two"})
    adapter.gates["m2"].set()
    await collect(runtime, second["id"])
    adapter.gates["m1"].set()
    await collect(runtime, first["id"])
    print(run["session_id"])

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

    async def close(self):
        return None

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    turn = await runtime.submit(sys.argv[2], {"id": "m3", "content": "three"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps(list(adapter.requests[0].context)))

asyncio.run(main())
'''


_SEED_OVERLAP_PROCESS = r'''
import asyncio, json, os, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.gates = {"m1": asyncio.Event(), "m2": asyncio.Event()}
    async def start(self, request): return object()
    async def submit(self, handle, request, emit):
        await self.gates[request.message_id].wait()
        return AdapterResult(result_text="answer:" + request.message_id)
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    first = await runtime.submit(run["session_id"], {"id": "m1", "content": "one"})
    second = await runtime.submit(run["session_id"], {"id": "m2", "content": "two"})
    adapter.gates["m1"].set()
    await collect(runtime, first["id"])
    print(json.dumps({"first": first["id"], "second": second["id"]}), flush=True)
    os._exit(0)

asyncio.run(main())
'''


_SKEW_PENDING_CONTEXT_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

root, value, mode = Path(sys.argv[1]), json.loads(sys.argv[2]), sys.argv[3]
entry = json.dumps([{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:m1"}])
connection = sqlite3.connect(root / "runs.sqlite3")
connection.execute("UPDATE turns SET context = ? WHERE id = ?", (entry, value["second"]))
if mode == "equal":
    moment, = connection.execute("SELECT time FROM events WHERE turn_id = ? AND seq = 0", (value["second"],)).fetchone()
else:
    moment = "2000-01-01T00:00:00+00:00"
connection.execute("UPDATE events SET time = ? WHERE turn_id = ? AND type = 'turn_end'", (moment, value["first"]))
connection.commit()
connection.close()
'''


_SKEW_COMPLETED_TIME_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.execute("UPDATE events SET time = '9999-01-01T00:00:00+00:00' WHERE turn_id = ? AND type = 'turn_end'", (sys.argv[2],))
connection.commit()
connection.close()
'''


_SKEW_ALL_TIMES_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
rows = connection.execute("SELECT rowid FROM events ORDER BY rowid").fetchall()
for index, (rowid,) in enumerate(rows):
    moment = "2026-01-01T00:00:00+00:00" if sys.argv[2] == "equal" else f"2026-01-01T00:00:{59 - index:02d}+00:00"
    connection.execute("UPDATE events SET time = ? WHERE rowid = ?", (moment, rowid))
connection.commit()
connection.close()
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

    async def close(self):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    first = await runtime.submit(run["session_id"], {"id": "first", "content": "one"})
    second = await runtime.submit(run["session_id"], {"id": "second", "content": "two"})
    await asyncio.sleep(0.1)
    print(json.dumps({"run_id": run["id"], "session_id": run["session_id"], "turn_id": first["id"], "first_turn": first["id"], "second_turn": second["id"]}), flush=True)
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

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    before = list(adapter.calls)
    first = await collect(runtime, sys.argv[2])
    second = await collect(runtime, sys.argv[3])
    duplicate = await runtime.submit(sys.argv[4], {"id": "first", "content": "changed"})
    resumed = await runtime.submit(sys.argv[4], {"id": "new", "content": "resume"})
    resumed_events = await collect(runtime, resumed["id"])
    print(json.dumps({"before": before, "first": first, "second": second, "duplicate": duplicate, "resumed": resumed_events, "calls": adapter.calls}))

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


_SECRET_LAUNCH_PROCESS = r'''
import asyncio, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return None
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    try:
        await runtime.launch({"adapter": "fake", "api_key_value": "sentinel"})
    except ValueError as error:
        print("rejected:" + str(error))
    else:
        print("accepted")

asyncio.run(main())
'''


_CORRUPT_SECRET_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
run_id = connection.execute("SELECT id FROM runs").fetchone()[0]
connection.execute("UPDATE runs SET agent_snapshot = ? WHERE id = ?", (json.dumps({"adapter": "fake", "api_key_value": "sentinel"}), run_id))
connection.commit()
connection.close()
'''


_CANCELLED_RESULT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit):
        return AdapterResult(status="cancelled", result_text="discard-me")
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"adapter": "fake"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "main", "content": "work"})
    events = await collect(runtime, turn["id"])
    duplicate = await runtime.submit(run["session_id"], {"id": "main", "content": "changed"})
    print(json.dumps({"session_id": run["session_id"], "turn_id": duplicate["id"], "turn": duplicate, "events": events}))

asyncio.run(main())
'''


_CANCELLED_MAIN_RESULT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit):
        return AdapterResult(status="cancelled", result_text="discard-me")
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"adapter": "fake"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "main", "content": "work"})
    events = await collect(runtime, turn["id"])
    print(json.dumps({"turn_id": turn["id"], "events": events}))

asyncio.run(main())
'''


_CORRUPT_CANCELLED_RESULT_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

root, value = Path(sys.argv[1]), json.loads(sys.argv[2])
turn_id = value["turn_id"]
bad_result = "corrupt-cancelled-result"
connection = sqlite3.connect(root / "runs.sqlite3")
connection.execute("UPDATE turns SET result_text = ? WHERE id = ?", (bad_result, turn_id))
seq, raw = connection.execute("SELECT seq, data FROM events WHERE turn_id = ? AND type = 'turn_end'", (turn_id,)).fetchone()
data = json.loads(raw)
data["result_text"] = bad_result
connection.execute("UPDATE events SET data = ? WHERE turn_id = ? AND seq = ?", (json.dumps(data), turn_id, seq))
connection.commit()
connection.close()
'''


_CORRUPT_MIDDLE_TURN_START_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

root, turn_id = Path(sys.argv[1]), sys.argv[2]
connection = sqlite3.connect(root / "runs.sqlite3")
run_id, = connection.execute("SELECT run_id FROM events WHERE turn_id = ? AND seq = 0", (turn_id,)).fetchone()
connection.execute("UPDATE events SET seq = seq + 10 WHERE turn_id = ? AND seq > 0", (turn_id,))
connection.execute("INSERT INTO events (turn_id, seq, run_id, type, time, data) VALUES (?, 1, ?, 'turn_start', 'corrupt-time', ?)", (turn_id, run_id, json.dumps({"message_id": "forged", "input": "forged"})))
connection.execute("UPDATE events SET seq = seq - 9 WHERE turn_id = ? AND seq > 1", (turn_id,))
assert [row[0] for row in connection.execute("SELECT seq FROM events WHERE turn_id = ? ORDER BY seq", (turn_id,))] == [0, 1, 2, 3]
connection.commit()
connection.close()
'''


_CORRUPT_RUNNING_TURN_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

root, value, corruption = Path(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
connection = sqlite3.connect(root / "runs.sqlite3")
connection.execute(
    "UPDATE turns SET result_text = ?, error = ? WHERE id = ?",
    (corruption.get("result_text"), corruption.get("error"), value["turn_id"]),
)
connection.commit()
connection.close()
'''


_PENDING_CONTEXT_PROCESS = r'''
import asyncio, json, os, sqlite3, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.requests = []
    async def start(self, request):
        self.requests.append(request)
        return object()
    async def submit(self, handle, request, emit):
        if request.message_id == "m1":
            return AdapterResult(result_text="answer:one")
        await asyncio.Event().wait()
    async def cancel(self, handle, request):
        return None

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    first = await runtime.submit(run["session_id"], {"id": "m1", "content": "one"})
    await collect(runtime, first["id"])
    second = await runtime.submit(run["session_id"], {"id": "m2", "content": "two"})
    while len(adapter.requests) < 2:
        await asyncio.sleep(0)
    connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
    stored = json.loads(connection.execute("SELECT context FROM turns WHERE id = ?", (second["id"],)).fetchone()[0])
    connection.close()
    print(json.dumps({"turn_id": second["id"], "adapter_context": list(adapter.requests[1].context), "stored_context": stored}), flush=True)
    os._exit(0)

asyncio.run(main())
'''


_CORRUPT_PENDING_CONTEXT_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.execute("UPDATE turns SET context = '[]' WHERE id = ?", (sys.argv[2],))
connection.commit()
connection.close()
'''


_REJECT_CORRUPT_RECOVERY_PROCESS = r'''
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

    async def close(self):
        return None

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


_RECOVER_CANCELLED_RESULT_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): raise AssertionError("recovery called adapter")
    async def cancel(self, handle, request): raise AssertionError("recovery called adapter")

    async def close(self):
        return None

async def collect(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    duplicate = await runtime.submit(sys.argv[2], {"id": "main", "content": "changed"})
    events = await collect(runtime, sys.argv[3])
    print(json.dumps({"session_id": sys.argv[2], "turn_id": duplicate["id"], "turn": duplicate, "events": events}))

asyncio.run(main())
'''


_REJECT_RECOVERY_PROCESS = r'''
import json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): raise AssertionError("recovery called adapter")
    async def submit(self, handle, request, emit): raise AssertionError("recovery called adapter")
    async def cancel(self, handle, request): raise AssertionError("recovery called adapter")

    async def close(self):
        return None

try:
    Runtime(Path(sys.argv[1]), {"fake": Adapter()})
except Exception as error:
    print(type(error).__name__ + ":" + str(error))
else:
    print("constructed")
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

    async def close(self):
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


def _assert_corrupt_cancelled_result_fails(tmp_path, seed):
    created = _output(_run_process(seed, tmp_path))
    _run_process(_CORRUPT_CANCELLED_RESULT_PROCESS, tmp_path, json.dumps(created))
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


def test_adapter_cannot_persist_runtime_owned_child_result(tmp_path):
    created = _output(_run_process(_RESERVED_EVENT_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_RESERVED_EVENT_PROCESS, tmp_path, created["attack_turn"], created["session_id"]))
    assert recovered["constructed"], recovered
    attack = created["attack"]
    assert [event["type"] for event in attack] == ["turn_start", "turn_end"]
    assert attack[-1]["data"] == {"status": "error", "result_text": None, "error": "adapter cannot emit runtime-owned event: child_result"}
    assert recovered["attack"] == attack
    assert recovered["duplicate"] == {"id": created["attack_turn"], "run_id": created["run_id"], "turn_id": created["attack_turn"], "message_id": "attack", "status": "error", "result_text": None}
    assert recovered["resumed"][-1]["data"] == {"status": "completed", "result_text": "resumed"}


def test_completed_run_recovers_in_a_fresh_interpreter(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_COMPLETED_PROCESS, tmp_path, created["session_id"], created["turn_id"]))
    assert recovered["before"] == []
    assert recovered["duplicate"]["id"] == created["turn_id"]
    assert recovered["replay"] == created["events"]
    assert recovered["context"] == [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:one"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:two"}]
    assert recovered["adapter"] == "fake"
    assert recovered["snapshot"] == {"id": "main", "adapter": "fake", "model": "frozen-model", "instructions": "frozen instructions", "tools": [], "params": {"mode": "frozen"}}
    assert recovered["calls"] == [["start", "fake", "m3"], ["submit", "fake", "m3"]]


def test_recovered_context_keeps_submit_order_after_reverse_completion(tmp_path):
    run_id = _run_process(_REVERSE_CONTEXT_PROCESS, tmp_path).stdout.strip()
    result = _run_process(_RECOVER_CONTEXT_PROCESS, tmp_path, run_id)
    assert json.loads(result.stdout) == [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:m1"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:m2"}]


_EXPECTED_COMPLETED_CONTEXT = [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:one"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:two"}]


@pytest.mark.parametrize("mode", ["equal", "earlier"], ids=["equal_timestamps", "reverse_rollback"])
def test_context_inclusion_beyond_causal_order_fails_on_fresh_construction(tmp_path, mode):
    created = _output(_run_process(_SEED_OVERLAP_PROCESS, tmp_path))
    _run_process(_SKEW_PENDING_CONTEXT_PROCESS, tmp_path, json.dumps(created), mode)
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all("error" in attempt for attempt in attempts), attempts
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


def test_backward_display_clock_keeps_valid_completed_history(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    _run_process(_SKEW_COMPLETED_TIME_PROCESS, tmp_path, created["first"][0]["turn_id"])
    result = _run_process(_RECOVER_CONTEXT_PROCESS, tmp_path, created["session_id"])
    assert json.loads(result.stdout) == _EXPECTED_COMPLETED_CONTEXT


@pytest.mark.parametrize("mode", ["equal", "decreasing"])
def test_multiple_active_turns_survive_restart_with_skewed_display_times(tmp_path, mode):
    run_id = _run_process(_REVERSE_CONTEXT_PROCESS, tmp_path).stdout.strip()
    _run_process(_SKEW_ALL_TIMES_PROCESS, tmp_path, mode)
    result = _run_process(_RECOVER_CONTEXT_PROCESS, tmp_path, run_id)
    assert json.loads(result.stdout) == [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:m1"}, {"role": "user", "message_id": "m2", "content": "two"}, {"role": "assistant", "content": "answer:m2"}]


def test_pending_root_turns_recover_in_a_fresh_interpreter(tmp_path):
    created = _output(_run_process(_CRASH_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_CRASH_PROCESS, tmp_path, created["first_turn"], created["second_turn"], created["session_id"]))
    expected = {"status": "error", "result_text": None, "error": "runtime restarted before turn completion"}
    assert recovered["before"] == []
    assert [event["type"] for event in recovered["first"]] == ["turn_start", "turn_end"]
    assert [event["type"] for event in recovered["second"]] == ["turn_start", "turn_end"]
    assert recovered["first"][-1]["data"] == expected
    assert recovered["second"][-1]["data"] == expected
    assert recovered["duplicate"]["status"] == "error"
    assert recovered["resumed"][-1]["data"]["status"] == "completed"
    assert recovered["calls"] == [["start", "new"], ["submit", "new"]]


def test_secret_agent_spec_is_rejected_before_launch_persists_a_run(tmp_path):
    result = _run_process(_SECRET_LAUNCH_PROCESS, tmp_path)
    assert result.stdout.startswith("rejected:")
    assert "api_key_value" in result.stdout


def test_persisted_secret_snapshot_fails_before_fresh_recovery(tmp_path):
    _run_process(_COMPLETED_PROCESS, tmp_path)
    _run_process(_CORRUPT_SECRET_PROCESS, tmp_path)
    result = _run_process(_FAIL_STARTUP_PROCESS, tmp_path)
    assert result.stdout.startswith("RunStoreError:runtime store")


def test_cancelled_adapter_result_is_identical_before_and_after_restart(tmp_path):
    created = _output(_run_process(_CANCELLED_RESULT_PROCESS, tmp_path))
    recovered = _output(_run_process(_RECOVER_CANCELLED_RESULT_PROCESS, tmp_path, created["session_id"], created["turn_id"]))
    assert recovered == created
    assert created["turn"]["result_text"] is None
    assert created["events"][-1]["data"] == {"status": "cancelled", "result_text": None}


def test_corrupt_cancelled_main_result_fails_before_fresh_recovery(tmp_path):
    _assert_corrupt_cancelled_result_fails(tmp_path, _CANCELLED_MAIN_RESULT_PROCESS)


def test_middle_turn_start_fails_before_fresh_recovery(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    assert [event["type"] for event in created["events"]] == ["turn_start", "delta", "turn_end"]
    _run_process(_CORRUPT_MIDDLE_TURN_START_PROCESS, tmp_path, created["turn_id"])
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all("error" in attempt for attempt in attempts), attempts
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all("duplicate turn start" in attempt["error"] for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


def test_pending_turn_context_mutation_fails_on_repeated_fresh_construction(tmp_path):
    created = _output(_run_process(_PENDING_CONTEXT_PROCESS, tmp_path))
    expected = [{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:one"}]
    assert created["adapter_context"] == expected
    assert created["stored_context"] == expected
    _run_process(_CORRUPT_PENDING_CONTEXT_PROCESS, tmp_path, created["turn_id"])
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all("error" in attempt for attempt in attempts), attempts
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


@pytest.mark.parametrize("corruption", [{"result_text": "corrupt"}, {"error": "corrupt"}, {"result_text": "corrupt", "error": "corrupt"}], ids=["result", "error", "both"])
def test_running_turn_with_terminal_fields_fails_before_fresh_recovery(tmp_path, corruption):
    created = _output(_run_process(_CRASH_PROCESS, tmp_path))
    _run_process(_CORRUPT_RUNNING_TURN_PROCESS, tmp_path, json.dumps(created), json.dumps(corruption))
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all("error" in attempt for attempt in attempts), attempts
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


def test_same_shape_store_with_missing_constraints_rejects_duplicate_submit_seq(tmp_path):
    _run_process(_CORRUPT_STORE_PROCESS, tmp_path)
    result = _run_process(_FAIL_STARTUP_PROCESS, tmp_path)
    assert result.stdout.startswith("RunStoreError:runtime store")


_MISSING_ADAPTER_PROCESS = """
from pathlib import Path
import sys
from runtime.runtime import Runtime
class Adapter:
    adapter_id = "other"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return None
    async def cancel(self, handle, request): return None

    async def close(self):
        return None
try:
    Runtime(Path(sys.argv[1]), {"other": Adapter()})
except ValueError as error:
    print(error)
"""


def test_missing_adapter_fails_startup_without_fallback(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    result = _run_process(_MISSING_ADAPTER_PROCESS, tmp_path, created["run_id"])
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


_DELETE_MIDDLE_EVENT_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.execute("DELETE FROM events WHERE turn_id = ? AND type = 'delta'", (sys.argv[2],))
connection.execute("UPDATE events SET seq = 1 WHERE turn_id = ? AND type = 'turn_end'", (sys.argv[2],))
connection.commit()
connection.close()
'''


_DELETE_LAST_EVENT_PROCESS = r'''
import json, sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
turn_id = sys.argv[2]
run_id, = connection.execute("SELECT run_id FROM turns WHERE id = ?", (turn_id,)).fetchone()
context = json.dumps([{"role": "user", "message_id": "m1", "content": "one"}, {"role": "assistant", "content": "answer:one"}])
connection.execute("DELETE FROM events WHERE turn_id = ? AND type = 'turn_end'", (turn_id,))
connection.execute("UPDATE turns SET status = 'running', result_text = NULL WHERE id = ?", (turn_id,))
connection.execute("UPDATE runs SET completed_context = ? WHERE id = ?", (context, run_id))
connection.commit()
connection.close()
'''


_DROP_EVENT_SEQUENCE_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.execute("DELETE FROM sqlite_sequence WHERE name = 'events'")
connection.commit()
connection.close()
'''


_SKEW_EVENT_SEQUENCE_PROCESS = r'''
import sqlite3, sys
from pathlib import Path

connection = sqlite3.connect(Path(sys.argv[1]) / "runs.sqlite3")
connection.execute("UPDATE sqlite_sequence SET seq = seq - 1 WHERE name = 'events'")
connection.commit()
connection.close()
'''


_LAUNCH_ONLY_PROCESS = r'''
import asyncio, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return None
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    print(run["session_id"])

asyncio.run(main())
'''


_RACE_SEED_PROCESS = r'''
import asyncio, json, os, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): await asyncio.Event().wait()
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-main")
    turn = await runtime.submit(run["session_id"], {"id": "m1", "content": "one"})
    await asyncio.sleep(0.1)
    print(json.dumps({"run_id": run["id"], "turn_id": turn["id"]}), flush=True)
    os._exit(0)

asyncio.run(main())
'''


_RACE_WRITER_PROCESS = r'''
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

    async def close(self):
        return None

adapter = Adapter()
try:
    Runtime(Path(sys.argv[1]), {"fake": adapter})
except Exception as error:
    print(json.dumps({"constructed": False, "error": type(error).__name__ + ":" + str(error), "calls": adapter.calls}))
else:
    print(json.dumps({"constructed": True, "calls": adapter.calls}))
'''


_RACE_READER_PROCESS = r'''
import json, subprocess, sys, time
from pathlib import Path
import runtime.run_store as store_module
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start")
    async def submit(self, handle, request, emit): self.calls.append("submit")
    async def cancel(self, handle, request): self.calls.append("cancel")

    async def close(self):
        return None

root = Path(sys.argv[1])
journal = root / "runs.sqlite3-journal"
writer_source = Path(sys.argv[2]).read_text()
writer = None
original = store_module._rows

def probed(connection, query, decoder):
    global writer
    rows = original(connection, query, decoder)
    if writer is None and "FROM turns" in query:
        writer = subprocess.Popen([sys.executable, "-c", writer_source, str(root)], stdout=subprocess.PIPE, text=True)
        while not journal.exists() and writer.poll() is None:
            time.sleep(0.001)
        try:
            writer.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
    return rows

store_module._rows = probed
adapter = Adapter()
try:
    Runtime(root, {"fake": adapter})
except Exception as error:
    outcome = {"constructed": False, "error": type(error).__name__ + ":" + str(error)}
else:
    outcome = {"constructed": True}
out, _ = writer.communicate()
print(json.dumps({"reader": outcome, "reader_calls": adapter.calls, "writer": json.loads(out)}))
'''


_RACE_REPLAY_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    async def start(self, request): return object()
    async def submit(self, handle, request, emit): return None
    async def cancel(self, handle, request): return None

    async def close(self):
        return None

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    events = [event async for event in runtime.subscribe(sys.argv[2])]
    print(json.dumps([{"seq": event["seq"], "type": event["type"], "data": event["data"]} for event in events]))

asyncio.run(main())
'''


def _assert_rejected_twice(tmp_path):
    attempts = [_output(_run_process(_REJECT_CORRUPT_RECOVERY_PROCESS, tmp_path)) for _ in range(2)]
    assert all("error" in attempt for attempt in attempts), attempts
    assert all(attempt["error"].startswith("RunStoreError:runtime store") for attempt in attempts)
    assert all(attempt["calls"] == [] and attempt["unchanged"] for attempt in attempts)
    assert attempts[0] == attempts[1]


def test_deleted_middle_event_fails_on_repeated_fresh_construction(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    _run_process(_DELETE_MIDDLE_EVENT_PROCESS, tmp_path, created["turn_id"])
    _assert_rejected_twice(tmp_path)


def test_deleted_last_event_fails_on_repeated_fresh_construction(tmp_path):
    created = _output(_run_process(_COMPLETED_PROCESS, tmp_path))
    _run_process(_DELETE_LAST_EVENT_PROCESS, tmp_path, created["turn_id"])
    _assert_rejected_twice(tmp_path)


def test_missing_event_sequence_metadata_fails_on_fresh_construction(tmp_path):
    _run_process(_COMPLETED_PROCESS, tmp_path)
    _run_process(_DROP_EVENT_SEQUENCE_PROCESS, tmp_path)
    _assert_rejected_twice(tmp_path)


def test_corrupt_event_sequence_metadata_fails_on_fresh_construction(tmp_path):
    _run_process(_COMPLETED_PROCESS, tmp_path)
    _run_process(_SKEW_EVENT_SEQUENCE_PROCESS, tmp_path)
    _assert_rejected_twice(tmp_path)


def test_launch_only_history_recovers_in_a_fresh_interpreter(tmp_path):
    run_id = _run_process(_LAUNCH_ONLY_PROCESS, tmp_path).stdout.strip()
    result = _run_process(_RECOVER_CONTEXT_PROCESS, tmp_path, run_id)
    assert json.loads(result.stdout) == []


def test_concurrent_constructors_never_observe_a_mixed_snapshot(tmp_path):
    created = _output(_run_process(_RACE_SEED_PROCESS, tmp_path))
    writer = tmp_path / "writer.py"
    writer.write_text(_RACE_WRITER_PROCESS)
    raced = _output(_run_process(_RACE_READER_PROCESS, tmp_path, str(writer)))
    assert raced["reader"] == {"constructed": True}, raced
    assert raced["reader_calls"] == [] and raced["writer"] == {"constructed": True, "calls": []}, raced
    replay = _output(_run_process(_RACE_REPLAY_PROCESS, tmp_path, created["turn_id"]))
    assert replay == [
        {"seq": 0, "type": "turn_start", "data": {"message_id": "m1", "input": "one"}},
        {"seq": 1, "type": "turn_end", "data": {"status": "error", "result_text": None, "error": "runtime restarted before turn completion"}},
    ]

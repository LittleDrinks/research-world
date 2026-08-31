import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from runtime.adapter import AdapterResult
from runtime.runtime import Runtime


SPEC = {"id": "main", "adapter": "fake"}


_FRESH_OWNER_PROCESS = r'''
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

async def main():
    runtime = Runtime(Path(sys.argv[1]), {"fake": Adapter()})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-a")
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "one"})
    [event async for event in runtime.subscribe(turn["id"])]
    print(json.dumps(await runtime.submit(run["id"], {"id": "message-1", "content": "one"})))

asyncio.run(main())
'''


_FRESH_READER_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start"); return object()
    async def submit(self, handle, request, emit): self.calls.append("submit")
    async def cancel(self, handle, request): self.calls.append("cancel")

async def main():
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    run = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-a")
    duplicate = await runtime.submit(run["id"], {"id": "message-1", "content": "changed"})
    other = await runtime.launch({"id": "main", "adapter": "fake"}, session_id="session-b")
    try:
        await runtime.submit(other["id"], {"id": "message-1", "content": "one"})
    except ValueError as error:
        conflict = str(error)
    else:
        conflict = "accepted"
    print(json.dumps({"duplicate": duplicate, "conflict": conflict, "calls": adapter.calls}))

asyncio.run(main())
'''


_RACE_PROCESS = r'''
import asyncio, json, sys
from pathlib import Path
from runtime.adapter import AdapterResult
from runtime.runtime import Runtime

class Adapter:
    adapter_id = "fake"
    supports_multiple_writers = True
    def __init__(self): self.calls = []
    async def start(self, request): self.calls.append("start"); return object()
    async def submit(self, handle, request, emit):
        self.calls.append("submit")
        return AdapterResult(result_text="answer")
    async def cancel(self, handle, request): self.calls.append("cancel")

async def main():
    ready, go = Path(sys.argv[2]), Path(sys.argv[3])
    ready.touch()
    while not go.exists(): await asyncio.sleep(0.001)
    adapter = Adapter()
    runtime = Runtime(Path(sys.argv[1]), {"fake": adapter})
    try:
        turn = await runtime.submit(sys.argv[4], {"id": "message-race", "content": "one"})
    except ValueError as error:
        result = {"status": "rejected", "error": str(error)}
    else:
        [event async for event in runtime.subscribe(turn["id"])]
        result = {"status": "accepted", "turn_id": turn["id"]}
    print(json.dumps({**result, "calls": adapter.calls}))

asyncio.run(main())
'''


class CountingAdapter:
    adapter_id = "fake"
    supports_multiple_writers = True

    def __init__(self):
        self.calls = []

    async def start(self, request):
        self.calls.append(("start", request.message_id))
        return object()

    async def submit(self, handle, request, emit):
        self.calls.append(("submit", request.message_id))
        return AdapterResult(result_text="answer")

    async def cancel(self, handle, request):
        self.calls.append(("cancel", request.message_id))


class HoldingAdapter(CountingAdapter):
    def __init__(self):
        super().__init__()
        self.release = asyncio.Event()

    async def submit(self, handle, request, emit):
        self.calls.append(("submit", request.message_id))
        await self.release.wait()
        return AdapterResult(status="cancelled")

    async def cancel(self, handle, request):
        self.calls.append(("cancel", request.message_id))
        self.release.set()


class ChildAdapter(CountingAdapter):
    adapter_id = "child"


async def _events(runtime, turn_id):
    return [event async for event in runtime.subscribe(turn_id)]


async def _launched_pair(tmp_path):
    first_adapter, second_adapter = HoldingAdapter(), HoldingAdapter()
    first = Runtime(tmp_path, {"fake": first_adapter})
    second = Runtime(tmp_path, {"fake": second_adapter})
    first_run = await first.launch(SPEC, session_id="session-a")
    second_run = await second.launch(SPEC, session_id="session-b")
    return (first, first_adapter, first_run), (second, second_adapter, second_run)


@pytest.mark.parametrize("winner_index", [0, 1], ids=["first_claim", "second_claim"])
@pytest.mark.asyncio
async def test_message_reuse_across_sessions_fails_before_execution(tmp_path, winner_index):
    pair = await _launched_pair(tmp_path)
    owner, loser = pair[winner_index], pair[1 - winner_index]
    owner_runtime, owner_adapter, owner_run = owner
    loser_runtime, loser_adapter, loser_run = loser
    turn = await owner_runtime.submit(owner_run["id"], {"id": "message-1", "content": "one"})

    with pytest.raises(ValueError, match="message belongs to another session"):
        await loser_runtime.submit(loser_run["id"], {"id": "message-1", "content": "one"})

    owner_adapter.release.set()
    assert (await _events(owner_runtime, turn["id"]))[-1]["data"]["status"] == "cancelled"
    assert owner_adapter.calls == [("start", "message-1"), ("submit", "message-1")]
    assert loser_adapter.calls == []


@pytest.mark.asyncio
async def test_message_ownership_survives_fresh_runtime(tmp_path):
    adapter = CountingAdapter()
    runtime = Runtime(tmp_path, {"fake": adapter})
    run = await runtime.launch(SPEC, session_id="session-a")
    turn = await runtime.submit(run["id"], {"id": "message-1", "content": "one"})
    await _events(runtime, turn["id"])
    restarted_adapter = CountingAdapter()
    restarted = Runtime(tmp_path, {"fake": restarted_adapter})
    other = await restarted.launch(SPEC, session_id="session-b")

    with pytest.raises(ValueError, match="message belongs to another session"):
        await restarted.submit(other["id"], {"id": "message-1", "content": "one"})

    assert restarted_adapter.calls == []


@pytest.mark.asyncio
async def test_same_message_and_session_reuses_turn_after_restart(tmp_path):
    runtime = Runtime(tmp_path, {"fake": CountingAdapter()})
    run = await runtime.launch(SPEC, session_id="session-a")
    original = await runtime.submit(run["id"], {"id": "message-1", "content": "one"})
    await _events(runtime, original["id"])
    restarted_adapter = CountingAdapter()
    restarted = Runtime(tmp_path, {"fake": restarted_adapter})
    recovered_run = await restarted.launch(SPEC, session_id="session-a")

    duplicate = await restarted.submit(recovered_run["id"], {"id": "message-1", "content": "changed"})

    assert duplicate == {**original, "status": "completed", "result_text": "answer"}
    assert restarted_adapter.calls == []


@pytest.mark.asyncio
async def test_child_reuse_of_session_message_fails_before_execution(tmp_path):
    parent_adapter, child_adapter = HoldingAdapter(), ChildAdapter()
    runtime = Runtime(tmp_path, {"fake": parent_adapter, "child": child_adapter})
    parent = await runtime.launch(SPEC, session_id="session-a")
    parent_turn = await runtime.submit(parent["id"], {"id": "message-1", "content": "one"})
    child = await runtime.delegate(parent["id"], {"id": "child", "adapter": "child"}, parent_turn_id=parent_turn["id"])

    with pytest.raises(ValueError, match="message belongs to another session"):
        await runtime.submit(child["id"], {"id": "message-1", "content": "one"})

    assert child_adapter.calls == []
    await runtime.cancel(parent_turn["id"])


@pytest.mark.asyncio
async def test_session_reuse_of_child_message_fails_before_execution(tmp_path):
    parent_adapter, child_adapter = HoldingAdapter(), ChildAdapter()
    runtime = Runtime(tmp_path, {"fake": parent_adapter, "child": child_adapter})
    parent = await runtime.launch(SPEC, session_id="session-a")
    other = await runtime.launch(SPEC, session_id="session-b")
    parent_turn = await runtime.submit(parent["id"], {"id": "message-1", "content": "one"})
    child = await runtime.delegate(parent["id"], {"id": "child", "adapter": "child"}, parent_turn_id=parent_turn["id"])
    child_turn = await runtime.submit(child["id"], {"id": "message-2", "content": "two"})
    assert (await _events(runtime, child_turn["id"]))[-1]["data"]["status"] == "completed"

    with pytest.raises(ValueError, match="message belongs to a child run"):
        await runtime.submit(other["id"], {"id": "message-2", "content": "two"})

    assert parent_adapter.calls == [("start", "message-1"), ("submit", "message-1")]
    await runtime.cancel(parent_turn["id"])


@pytest.mark.asyncio
async def test_concurrent_cross_session_claim_has_one_execution_winner(tmp_path):
    pair = await _launched_pair(tmp_path)
    attempts = await asyncio.gather(
        *(runtime.submit(run["id"], {"id": "message-1", "content": "one"}) for runtime, _, run in pair),
        return_exceptions=True,
    )
    winner_index = next(index for index, value in enumerate(attempts) if isinstance(value, dict))
    loser_index = 1 - winner_index
    pair[winner_index][1].release.set()
    await _events(pair[winner_index][0], attempts[winner_index]["id"])

    assert isinstance(attempts[loser_index], ValueError)
    assert pair[winner_index][1].calls == [("start", "message-1"), ("submit", "message-1")]
    assert pair[loser_index][1].calls == []


def _run_process(script, root, *arguments):
    command = [sys.executable, "-c", script, str(root), *arguments]
    return subprocess.run(command, cwd=Path(__file__).parents[1], check=True, capture_output=True, text=True, timeout=5)


def _start_race_process(root, ready, go, run_id):
    command = [sys.executable, "-c", _RACE_PROCESS, str(root), str(ready), str(go), run_id]
    return subprocess.Popen(command, cwd=Path(__file__).parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _wait_for_ready(paths):
    for _ in range(500):
        if all(path.exists() for path in paths):
            return
        time.sleep(0.01)
    raise AssertionError("race processes did not become ready")


def _race_results(processes):
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        results.append(json.loads(stdout))
    return results


@pytest.mark.asyncio
async def test_message_ownership_survives_fresh_interpreter(tmp_path):
    owner = json.loads(_run_process(_FRESH_OWNER_PROCESS, tmp_path).stdout)
    recovered = json.loads(_run_process(_FRESH_READER_PROCESS, tmp_path).stdout)

    assert recovered["duplicate"] == owner
    assert recovered["conflict"] == "message belongs to another session"
    assert recovered["calls"] == []


@pytest.mark.asyncio
async def test_process_race_has_one_owner_and_zero_loser_execution(tmp_path):
    runtime = Runtime(tmp_path, {"fake": CountingAdapter()})
    first = await runtime.launch(SPEC, session_id="session-a")
    second = await runtime.launch(SPEC, session_id="session-b")
    go = tmp_path / "go"
    processes = [
        _start_race_process(tmp_path, tmp_path / "ready-a", go, first["id"]),
        _start_race_process(tmp_path, tmp_path / "ready-b", go, second["id"]),
    ]
    _wait_for_ready((tmp_path / "ready-a", tmp_path / "ready-b"))
    go.touch()
    results = _race_results(processes)

    assert [result["status"] for result in results].count("accepted") == 1
    assert [result["status"] for result in results].count("rejected") == 1
    rejected = next(result for result in results if result["status"] == "rejected")
    assert rejected["error"] == "message belongs to another session"
    assert sorted(result["calls"] for result in results) == [[], ["start", "submit"]]

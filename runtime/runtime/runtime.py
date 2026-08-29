from __future__ import annotations

import asyncio
import json
import threading
import uuid
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from inspect import isawaitable
from pathlib import Path
from typing import Any, Protocol


class RuntimeAdapter(Protocol):
    adapter_id: str
    supports_multiple_writers: bool

    async def start(self, request: TurnRequest) -> Any: ...

    async def submit(self, handle: Any, request: TurnRequest, emit) -> Any: ...

    async def cancel(self, handle: Any) -> Any: ...


@dataclass(frozen=True)
class TurnRequest:
    run_id: str
    turn_id: str
    message_id: str
    input: Any
    context: tuple[dict[str, Any], ...]
    agent_snapshot: dict[str, Any]


@dataclass(frozen=True)
class AdapterResult:
    status: str = "completed"
    result_text: str | None = None


class TraceLedger:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else None
        if self.root:
            self.root.mkdir(parents=True, exist_ok=True)
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
        self._watchers: defaultdict[str, set[asyncio.Queue]] = defaultdict(set)

    def append(self, turn_id: str, event_type: str, data: dict[str, Any], run_id: str):
        with self._locks[turn_id]:
            events = self._load(turn_id)
            event = _event(run_id, turn_id, len(events), event_type, data)
            self._write(turn_id, event)
            events.append(event)
        for queue in tuple(self._watchers[turn_id]):
            queue.put_nowait(deepcopy(event))
        return deepcopy(event)

    def read(self, turn_id: str, after_seq: int = -1):
        return [
            deepcopy(event)
            for event in self._load(turn_id)
            if event["seq"] > after_seq
        ]

    def exists(self, turn_id: str) -> bool:
        return bool(self._load(turn_id))

    def terminal(self, turn_id: str) -> bool:
        return any(event["type"] == "turn_end" for event in self._load(turn_id))

    def watch(self, turn_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._watchers[turn_id].add(queue)
        return queue

    def unwatch(self, turn_id: str, queue: asyncio.Queue) -> None:
        self._watchers[turn_id].discard(queue)

    def _load(self, turn_id: str) -> list[dict[str, Any]]:
        if turn_id in self._events:
            return self._events[turn_id]
        path = self._path(turn_id)
        if not path or not path.exists():
            events: list[dict[str, Any]] = []
        else:
            events = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line
            ]
        self._events[turn_id] = events
        return events

    def _write(self, turn_id: str, event: dict[str, Any]) -> None:
        path = self._path(turn_id)
        if not path:
            return
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
            stream.write("\n")

    def _path(self, turn_id: str) -> Path | None:
        if not self.root:
            return None
        if Path(turn_id).name != turn_id:
            raise ValueError("invalid turn id")
        return self.root / f"{turn_id}.jsonl"


@dataclass
class _Run:
    id: str
    agent_snapshot: dict[str, Any]
    adapter: RuntimeAdapter
    parent_run_id: str | None
    session_id: str | None
    context: list[dict[str, Any]] = field(default_factory=list)
    turns: dict[str, _Turn] = field(default_factory=dict)


@dataclass
class _Turn:
    request: TurnRequest
    adapter: RuntimeAdapter
    status: str = "running"
    result_text: str | None = None
    handle: Any = None
    cancel_requested: bool = False
    cancel_sent: bool = False
    task: asyncio.Task | None = None
    event_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class Runtime:
    def __init__(
        self,
        adapters: RuntimeAdapter | list[RuntimeAdapter] | dict[str, RuntimeAdapter],
        *,
        data_root: Path | None = None,
    ):
        self._adapters = _adapter_map(adapters)
        trace_root = Path(data_root) / "traces" if data_root else None
        self._trace = TraceLedger(trace_root)
        self._runs: dict[str, _Run] = {}
        self._turns: dict[str, _Turn] = {}
        self._registry_lock = asyncio.Lock()

    async def launch(
        self,
        agent_spec: dict[str, Any],
        *,
        session_id: str | None = None,
        parent_run_id: str | None = None,
    ) -> dict[str, Any]:
        snapshot = _snapshot(agent_spec)
        async with self._registry_lock:
            run = self._register_run(snapshot, session_id, parent_run_id)
        return _run_view(run)

    def _register_run(self, snapshot, session_id, parent_run_id):
        if parent_run_id:
            self._require_run(parent_run_id)
        adapter = _select_adapter(self._adapters, snapshot)
        run = _Run(
            f"r-{uuid.uuid4().hex}", snapshot, adapter, parent_run_id, session_id
        )
        self._runs[run.id] = run
        return run

    async def submit(
        self,
        run_id: str,
        message: dict[str, Any] | str,
        content: Any = None,
    ) -> dict[str, Any]:
        message_id, payload = _message(message, content)
        async with self._registry_lock:
            run = self._require_run(run_id)
            if existing := run.turns.get(message_id):
                return _turn_view(existing)
            turn_id = f"t-{uuid.uuid4().hex}"
            request = _request(run, turn_id, message_id, payload)
            turn = _Turn(request, run.adapter)
            run.turns[message_id] = turn
            self._turns[turn_id] = turn
            self._trace.append(turn_id, "turn_start", _start_data(request), run.id)
            turn.task = asyncio.create_task(self._execute(turn))
        return _turn_view(turn)

    def subscribe(self, turn_id: str, after_seq: int = -1):
        return self._subscribe(turn_id, _after_seq(after_seq))

    async def _subscribe(self, turn_id: str, after_seq: int):
        self._require_trace(turn_id)
        queue = self._trace.watch(turn_id)
        cursor = after_seq
        try:
            while True:
                values = self._trace.read(turn_id, cursor)
                for event in values:
                    cursor = event["seq"]
                    yield event
                    if event["type"] == "turn_end":
                        return
                if values:
                    continue
                if self._trace.terminal(turn_id):
                    return
                await queue.get()
        finally:
            self._trace.unwatch(turn_id, queue)

    async def cancel(self, turn_id: str) -> dict[str, Any]:
        turn = self._turn(turn_id)
        async with turn.event_lock:
            if turn.status != "running":
                return _turn_view(turn)
            turn.cancel_requested = True
        await self._finish(turn, "cancelled", None)
        await self._cancel_handle(turn)
        return _turn_view(turn)

    async def delegate(
        self,
        parent_run_id: str,
        agent_spec: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._registry_lock:
            self._require_run(parent_run_id)
        return await self.launch(agent_spec, parent_run_id=parent_run_id)

    async def _execute(self, turn: _Turn) -> None:
        try:
            if turn.cancel_requested:
                return
            turn.handle = await turn.adapter.start(turn.request)
            if turn.cancel_requested:
                await self._cancel_handle(turn)
                return
            result = await turn.adapter.submit(
                turn.handle, turn.request, lambda value: self._emit(turn, value)
            )
            await self._finish(turn, *_result(result))
        except asyncio.CancelledError:
            await self._finish(turn, "cancelled", None)
        except Exception as error:
            await self._finish(turn, "error", None, str(error))

    async def _emit(self, turn: _Turn, value: Any) -> None:
        event_type, data = _adapter_event(value)
        if event_type == "turn_end":
            raise RuntimeError("adapter cannot emit a terminal event")
        async with turn.event_lock:
            if turn.status == "running":
                self._trace.append(
                    turn.request.turn_id, event_type, data, turn.request.run_id
                )

    async def _finish(
        self,
        turn,
        status,
        result_text,
        error=None,
    ) -> None:
        async with turn.event_lock:
            if turn.status != "running":
                return
            status = _finish_status(turn, status)
            turn.status, turn.result_text = status, result_text
            self._append_end(turn, status, result_text, error)
            if status in {"completed", "limit"}:
                self._record_context(turn, result_text)

    def _append_end(self, turn, status, result_text, error):
        self._trace.append(
            turn.request.turn_id,
            "turn_end",
            _end_data(status, result_text, error),
            turn.request.run_id,
        )

    async def _cancel_handle(self, turn: _Turn) -> None:
        if turn.handle is None or turn.cancel_sent:
            return
        turn.cancel_sent = True
        result = turn.adapter.cancel(turn.handle)
        if isawaitable(result):
            await result

    def _record_context(self, turn: _Turn, result_text: str | None) -> None:
        run = self._runs[turn.request.run_id]
        run.context.extend(
            (
                {
                    "role": "user",
                    "message_id": turn.request.message_id,
                    "content": deepcopy(turn.request.input),
                },
                {"role": "assistant", "content": result_text or ""},
            )
        )

    def _require_trace(self, turn_id: str) -> None:
        if not self._trace.exists(turn_id):
            raise KeyError(f"turn not found: {turn_id}")

    def _require_run(self, run_id: str) -> _Run:
        try:
            return self._runs[run_id]
        except KeyError:
            raise KeyError(f"run not found: {run_id}") from None

    def _turn(self, turn_id: str) -> _Turn:
        try:
            return self._turns[turn_id]
        except KeyError:
            raise KeyError(f"turn not found: {turn_id}") from None


def _adapter_map(adapters) -> dict[str, RuntimeAdapter]:
    values = (
        list(adapters.items())
        if isinstance(adapters, dict)
        else _adapter_values(adapters)
    )
    result = dict(values)
    if len(result) != len(values):
        raise ValueError("adapter ids must be unique")
    return result


def _adapter_values(adapters):
    if hasattr(adapters, "start"):
        adapters = [adapters]
    values = list(adapters)
    return [(_adapter_id(adapter), adapter) for adapter in values]


def _adapter_id(adapter) -> str:
    if value := getattr(adapter, "adapter_id", None):
        return value
    descriptor = getattr(adapter, "descriptor", None)
    if descriptor and getattr(descriptor, "id", None):
        return descriptor.id
    raise ValueError("runtime adapter must declare adapter_id")


def _select_adapter(adapters, snapshot):
    requested = snapshot.get("adapter")
    runtime = snapshot.get("runtime")
    if requested is None and isinstance(runtime, dict):
        requested = runtime.get("id")
    if requested:
        try:
            return adapters[requested]
        except KeyError:
            raise ValueError(f"runtime adapter is unavailable: {requested}") from None
    if len(adapters) == 1:
        return next(iter(adapters.values()))
    raise ValueError("agent spec must select a runtime adapter")


def _snapshot(agent_spec) -> dict[str, Any]:
    if hasattr(agent_spec, "snapshot"):
        agent_spec = agent_spec.snapshot()
    if not isinstance(agent_spec, dict):
        raise TypeError("agent spec must be a mapping")
    return deepcopy(agent_spec)


def _message(message, content):
    if isinstance(message, dict):
        message_id = message.get("id") or message.get("message_id")
        payload = message.get("content", message.get("input"))
    elif isinstance(message, str) and content is not None:
        message_id, payload = message, content
    else:
        raise TypeError("submit requires a message id and content")
    if not isinstance(message_id, str) or not message_id:
        raise ValueError("message must have an id")
    return message_id, deepcopy(payload)


def _request(run, turn_id, message_id, payload):
    return TurnRequest(
        run.id,
        turn_id,
        message_id,
        payload,
        tuple(deepcopy(run.context)),
        deepcopy(run.agent_snapshot),
    )


def _start_data(request):
    return {"message_id": request.message_id, "input": deepcopy(request.input)}


def _adapter_event(value):
    if isinstance(value, str):
        return value, {}
    if not isinstance(value, dict):
        raise TypeError("adapter events must be mappings")
    event_type = value.get("type", "adapter_event")
    data = value.get("data")
    return event_type, deepcopy(data if isinstance(data, dict) else value)


def _result(value):
    if isinstance(value, AdapterResult):
        return value.status, value.result_text
    if isinstance(value, dict):
        return value.get("status", "completed"), value.get(
            "result_text", value.get("output", value.get("result"))
        )
    if isinstance(value, str):
        return "completed", value
    return "completed", None


def _status(status):
    if status not in {"completed", "limit", "error", "cancelled"}:
        return "error"
    return status


def _finish_status(turn, status):
    return "cancelled" if turn.cancel_requested else _status(status)


def _end_data(status, result_text, error):
    data = {
        "status": status,
        "result_text": None if status == "cancelled" else result_text,
    }
    if error:
        data["error"] = error
    return data


def _after_seq(value):
    if value is None:
        return -1
    if not isinstance(value, int):
        raise TypeError("after_seq must be an integer")
    return value


def _event(run_id, turn_id, seq, event_type, data):
    return {
        "run_id": run_id,
        "turn_id": turn_id,
        "seq": seq,
        "type": event_type,
        "time": datetime.now(UTC).isoformat(),
        "data": deepcopy(data),
    }


def _run_view(run):
    return {
        "id": run.id,
        "run_id": run.id,
        "parent_run_id": run.parent_run_id,
        "session_id": run.session_id,
        "agent_snapshot": deepcopy(run.agent_snapshot),
    }


def _turn_view(turn):
    return {
        "id": turn.request.turn_id,
        "turn_id": turn.request.turn_id,
        "run_id": turn.request.run_id,
        "message_id": turn.request.message_id,
        "status": turn.status,
        "result_text": turn.result_text,
    }

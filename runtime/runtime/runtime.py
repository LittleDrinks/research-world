from __future__ import annotations

import asyncio
import json
import threading
import uuid
from collections import defaultdict
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from inspect import iscoroutinefunction
from pathlib import Path
from typing import Any

from .adapter import (
    AdapterResult as _AdapterResult,
    RuntimeAdapter as _RuntimeAdapter,
    TurnRequest as _TurnRequest,
)
from .runtime_tools import KernelInterface, RuntimeTools


class TraceLedger:
    def __init__(self, root: Path):
        self.root = root
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
        if not path.exists():
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
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
            stream.write("\n")

    def _path(self, turn_id: str) -> Path:
        if Path(turn_id).name != turn_id:
            raise ValueError("invalid turn id")
        return self.root / f"{turn_id}.jsonl"


@dataclass
class _Run:
    id: str
    agent_snapshot: dict[str, Any]
    adapter: _RuntimeAdapter
    parent_run_id: str | None
    session_id: str | None
    tools: RuntimeTools
    context: list[dict[str, Any]] = field(default_factory=list)
    turns: dict[str, _Turn] = field(default_factory=dict)


@dataclass
class _Turn:
    request: _TurnRequest
    adapter: _RuntimeAdapter
    session_id: str | None
    status: str = "running"
    result_text: str | None = None
    handle: Any = None
    cancel_requested: bool = False
    task_cancel_requested: bool = False
    cancel_sent: bool = False
    task: asyncio.Task | None = None
    adapter_finished: bool = False
    accepting_children: bool = True
    waiting_for_children: bool = False
    child_turn_ids: set[str] = field(default_factory=set)
    terminal_event: asyncio.Event = field(default_factory=asyncio.Event)
    cancel_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class Runtime:
    def __init__(
        self,
        data_root: Path,
        adapters: dict[str, _RuntimeAdapter],
        *,
        kernel: KernelInterface | None = None,
    ):
        _require_data_root(data_root)
        self._adapters = _adapter_map(adapters)
        self._kernel = kernel
        self._trace = TraceLedger(data_root / "traces")
        self._runs: dict[str, _Run] = {}
        self._turns: dict[str, _Turn] = {}
        self._delegations: dict[str, tuple[str, str]] = {}
        self._adapter_reservations: dict[int, _Turn] = {}
        self._registry_lock = asyncio.Lock()

    async def launch(
        self,
        agent_spec: Mapping[str, Any],
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        snapshot = _snapshot(agent_spec)
        async with self._registry_lock:
            run = self._register_run(snapshot, session_id, None)
        return _run_view(run)

    def _register_run(self, snapshot, session_id, parent_run_id):
        if parent_run_id:
            self._require_run(parent_run_id)
        adapter = _select_adapter(self._adapters, snapshot)
        run = _Run(
            f"r-{uuid.uuid4().hex}",
            snapshot,
            adapter,
            parent_run_id,
            session_id,
            RuntimeTools(self._kernel, snapshot.get("tools", ())),
        )
        self._runs[run.id] = run
        return run

    async def submit(
        self,
        run_id: str,
        message: Mapping[str, Any],
    ) -> dict[str, Any]:
        message_id, payload = _message(message)
        async with self._registry_lock:
            turn = self._register_turn(run_id, message_id, payload)
        return _turn_view(turn)

    def _register_turn(self, run_id, message_id, payload):
        run = self._require_run(run_id)
        if existing := run.turns.get(message_id):
            return existing
        self._require_child_submit(run)
        turn_id = f"t-{uuid.uuid4().hex}"
        request = _request(run, turn_id, message_id, payload)
        turn = _Turn(request, run.adapter, run.session_id)
        run.turns[message_id] = turn
        self._turns[turn_id] = turn
        self._track_child_turn(run, turn)
        self._trace.append(turn_id, "turn_start", _start_data(request), run.id)
        self._start_turn(turn)
        return turn

    def _start_turn(self, turn):
        if self._reserve_adapter(turn):
            turn.task = asyncio.create_task(self._execute(turn))
        else:
            self._reject_turn(turn)

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
        async with turn.cancel_lock:
            async with self._registry_lock:
                if turn.status != "running":
                    return _turn_view(turn)
                turn.cancel_requested = True
                turn.accepting_children = False
            try:
                await self._stop_execution(turn)
            except Exception as error:
                await self._finish(turn, "error", None, str(error), force=True)
            else:
                await self._finish(turn, "cancelled", None, force=True)
        return _turn_view(turn)

    async def delegate(
        self,
        parent_run_id: str,
        agent_spec: Mapping[str, Any],
        *,
        parent_turn_id: str,
    ) -> dict[str, Any]:
        snapshot = _snapshot(agent_spec)
        async with self._registry_lock:
            self._require_parent_turn(parent_run_id, parent_turn_id)
            run = self._register_run(snapshot, None, parent_run_id)
            self._delegations[run.id] = (parent_run_id, parent_turn_id)
        return _run_view(run)

    async def _execute(self, turn: _Turn) -> None:
        try:
            await self._run_adapter(turn)
        except asyncio.CancelledError as error:
            await self._mark_adapter_finished(turn)
            await self._handle_cancelled(turn, error)
        except Exception as error:
            await self._mark_adapter_finished(turn)
            await self._finish(
                turn, "error", None, str(error), force=turn.cancel_requested
            )

    async def _run_adapter(self, turn: _Turn) -> None:
        if turn.cancel_requested:
            return
        turn.handle = await turn.adapter.start(turn.request)
        if turn.handle is None:
            raise RuntimeError("adapter start must return an execution handle")
        if turn.cancel_requested:
            return
        result = await turn.adapter.submit(
            turn.handle, turn.request, lambda value: self._emit(turn, value)
        )
        await self._mark_adapter_finished(turn)
        status, result_text = _result(result)
        await self._finish(turn, status, result_text)

    async def _mark_adapter_finished(self, turn: _Turn) -> None:
        async with self._registry_lock:
            turn.adapter_finished = True

    async def _handle_cancelled(
        self, turn: _Turn, error: asyncio.CancelledError
    ) -> None:
        if not turn.task_cancel_requested:
            await self._finish(
                turn,
                "error",
                None,
                _cancel_detail(error),
                force=turn.cancel_requested,
            )

    async def _emit(self, turn: _Turn, value: Any) -> None:
        event_type, data = _adapter_event(value)
        if event_type == "turn_end":
            raise RuntimeError("adapter cannot emit a terminal event")
        async with self._registry_lock:
            if turn.status == "running":
                self._trace.append(
                    turn.request.turn_id, event_type, data, turn.request.run_id
                )

    async def _finish(
        self, turn, status, result_text, error=None, *, force=False
    ) -> None:
        async with self._registry_lock:
            status = self._prepare_finish(turn, status, force)
            if status is None:
                return
            children = self._children_to_wait(turn, force)
            if not children:
                self._finish_locked(turn, status, result_text, error, force)
                return
        await self._wait_for_children(children)
        await self._finish_after_children(turn, status, result_text, error, force)

    def _prepare_finish(self, turn, status, force):
        if turn.status != "running":
            return None
        status = _status(status)
        if turn.cancel_requested and not force and status != "error":
            return None
        return status

    async def _finish_after_children(
        self, turn, status, result_text, error, force
    ) -> None:
        async with self._registry_lock:
            if turn.status == "running":
                self._finish_locked(turn, status, result_text, error, force)

    def _finish_locked(self, turn, status, result_text, error, force) -> None:
        if turn.status != "running":
            return
        status = _status(status)
        if turn.cancel_requested and not force and status != "error":
            return
        turn.status, turn.result_text = status, result_text
        turn.waiting_for_children = False
        self._append_end(turn, status, result_text, error)
        self._record_child_result(turn, status, result_text, error)
        self._release_adapter(turn)
        if status in {"completed", "limit"}:
            self._record_context(turn, result_text)
        turn.terminal_event.set()

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
        try:
            await turn.adapter.cancel(turn.handle, turn.request)
        except asyncio.CancelledError as error:
            raise RuntimeError(_cancel_detail(error)) from error

    async def _stop_execution(self, turn: _Turn) -> None:
        if turn.waiting_for_children:
            await self._cancel_execution_task(turn)
            return
        if turn.adapter_finished:
            return
        if turn.task is None:
            return
        if turn.handle is None:
            await self._cancel_execution_task(turn)
        if turn.handle is None:
            return
        try:
            await self._cancel_handle(turn)
        except Exception:
            await self._cancel_execution_task(turn)
            raise
        await self._wait_execution(turn)

    async def _cancel_execution_task(self, turn: _Turn) -> None:
        turn.task_cancel_requested = True
        turn.task.cancel()
        await self._wait_execution(turn)

    def _reserve_adapter(self, turn: _Turn) -> bool:
        if turn.adapter.supports_multiple_writers:
            return True
        adapter_key = id(turn.adapter)
        if adapter_key in self._adapter_reservations:
            return False
        self._adapter_reservations[adapter_key] = turn
        return True

    def _release_adapter(self, turn: _Turn) -> None:
        adapter_key = id(turn.adapter)
        if self._adapter_reservations.get(adapter_key) is turn:
            del self._adapter_reservations[adapter_key]

    def _reject_turn(self, turn: _Turn) -> None:
        turn.adapter_finished = True
        turn.accepting_children = False
        self._finish_locked(
            turn,
            "error",
            None,
            "adapter does not support overlapping active turns",
            True,
        )

    async def _wait_execution(self, turn: _Turn) -> None:
        if turn.task is None:
            return
        try:
            await turn.task
        except asyncio.CancelledError:
            return

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

    def _require_parent_turn(self, parent_run_id: str, parent_turn_id: str) -> None:
        if not isinstance(parent_turn_id, str) or not parent_turn_id:
            raise ValueError("parent_turn_id must be a nonempty string")
        turn = self._turn(parent_turn_id)
        if turn.request.run_id != parent_run_id:
            raise ValueError("parent turn belongs to another run")
        if turn.status != "running":
            raise ValueError("parent turn must be running")
        if turn.adapter_finished or not turn.accepting_children:
            raise ValueError("parent turn is no longer accepting child turns")

    def _require_child_submit(self, run: _Run) -> None:
        link = self._delegations.get(run.id)
        if link is None:
            return
        parent = self._turn(link[1])
        if parent.status != "running" or parent.adapter_finished or not parent.accepting_children:
            raise ValueError("parent turn is no longer accepting child turns")

    def _track_child_turn(self, run: _Run, turn: _Turn) -> None:
        link = self._delegations.get(run.id)
        if link is not None:
            self._turn(link[1]).child_turn_ids.add(turn.request.turn_id)

    def _children_to_wait(self, turn: _Turn, force: bool) -> tuple[_Turn, ...]:
        turn.accepting_children = False
        if force:
            return ()
        children = tuple(self._turns[child_id] for child_id in turn.child_turn_ids)
        turn.waiting_for_children = bool(children)
        return children

    async def _wait_for_children(self, children: tuple[_Turn, ...]) -> None:
        await asyncio.gather(*(child.terminal_event.wait() for child in children))

    def _record_child_result(self, turn, status, result_text, error) -> None:
        link = self._delegations.get(turn.request.run_id)
        if link is None:
            return
        parent_run_id, parent_turn_id = link
        if self._turn(parent_turn_id).status != "running":
            return
        self._trace.append(
            parent_turn_id,
            "child_result",
            _child_result_data(turn, status, result_text, error),
            parent_run_id,
        )

    def _turn(self, turn_id: str) -> _Turn:
        try:
            return self._turns[turn_id]
        except KeyError:
            raise KeyError(f"turn not found: {turn_id}") from None


def _adapter_map(adapters) -> dict[str, _RuntimeAdapter]:
    if not isinstance(adapters, dict):
        raise TypeError("adapters must be a dict")
    if any(not isinstance(key, str) or not key for key in adapters):
        raise TypeError("adapter ids must be nonempty strings")
    if any(not _is_adapter(adapter) for adapter in adapters.values()):
        raise TypeError("adapters must implement RuntimeAdapter")
    if any(adapter.adapter_id != key for key, adapter in adapters.items()):
        raise ValueError("adapter registry key must match adapter_id")
    return dict(adapters)


def _is_adapter(adapter):
    methods = ("start", "submit", "cancel")
    return (
        all(iscoroutinefunction(getattr(adapter, name, None)) for name in methods)
        and isinstance(getattr(adapter, "adapter_id", None), str)
        and bool(getattr(adapter, "adapter_id", None))
        and isinstance(getattr(adapter, "supports_multiple_writers", None), bool)
    )


def _require_data_root(data_root):
    if not isinstance(data_root, Path):
        raise TypeError("data_root must be a Path")


def _select_adapter(adapters, snapshot):
    adapter_id = snapshot["adapter"]
    try:
        return adapters[adapter_id]
    except KeyError:
        raise ValueError(f"runtime adapter is unavailable: {adapter_id}") from None


def _snapshot(agent_spec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(agent_spec, Mapping):
        raise TypeError("agent spec must be a mapping")
    snapshot = deepcopy(dict(agent_spec))
    if "runtime" in snapshot:
        raise ValueError("agent spec must use adapter")
    adapter_id = snapshot.get("adapter")
    if not isinstance(adapter_id, str) or not adapter_id:
        raise ValueError("agent spec must select an adapter")
    return snapshot


def _message(message: Mapping[str, Any]):
    if not isinstance(message, Mapping) or set(message) != {"id", "content"}:
        raise TypeError("submit requires an id/content message mapping")
    message_id = message["id"]
    if not isinstance(message_id, str) or not message_id:
        raise ValueError("message must have an id")
    return message_id, deepcopy(message["content"])


def _request(run, turn_id, message_id, payload):
    return _TurnRequest(
        run.id,
        turn_id,
        message_id,
        payload,
        tuple(deepcopy(run.context)),
        deepcopy(run.agent_snapshot),
        run.tools,
    )


def _start_data(request):
    return {"message_id": request.message_id, "input": deepcopy(request.input)}


def _adapter_event(value):
    if not isinstance(value, dict) or set(value) != {"type", "data"}:
        raise TypeError("adapter events must be type/data mappings")
    event_type, data = value["type"], value["data"]
    if not isinstance(event_type, str) or not event_type:
        raise ValueError("adapter event type must be nonempty")
    if not isinstance(data, dict):
        raise TypeError("adapter event data must be a dict")
    return event_type, deepcopy(data)


def _result(value: _AdapterResult):
    if not isinstance(value, _AdapterResult):
        raise TypeError("adapter submit must return AdapterResult")
    if value.result_text is not None and not isinstance(value.result_text, str):
        raise TypeError("adapter result_text must be a string or None")
    return value.status, value.result_text


def _cancel_detail(error: asyncio.CancelledError) -> str:
    return str(error) or "adapter operation was cancelled"


def _status(status):
    if status not in {"completed", "limit", "error", "cancelled"}:
        raise ValueError(f"invalid turn status: {status}")
    return status


def _end_data(status, result_text, error):
    data = {
        "status": status,
        "result_text": None if status == "cancelled" else result_text,
    }
    if error:
        data["error"] = error
    return data


def _child_result_data(turn, status, result_text, error):
    data = {
        "child_run_id": turn.request.run_id,
        "child_turn_id": turn.request.turn_id,
        "status": status,
        "result_text": result_text,
    }
    if error:
        data["error"] = error
    return data


def _after_seq(value):
    if not isinstance(value, int) or isinstance(value, bool):
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
        "session_id": turn.session_id,
        "message_id": turn.request.message_id,
        "status": turn.status,
        "result_text": turn.result_text,
    }

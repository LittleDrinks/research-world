from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class RunStoreError(ValueError):
    pass


_FORMAT = {"format": "runtime-run-store", "version": "1"}
_STATUSES = {"running", "completed", "limit", "cancelled", "error"}
_AGENT_SPEC_FIELDS = ("id", "adapter", "model", "instructions", "thinking", "workspace", "tools", "params")
_AGENT_TEXT_FIELDS = frozenset(_AGENT_SPEC_FIELDS) - {"tools", "params"}
_AGENT_PARAMS_FIELDS = frozenset({"mode"})
_TABLE_COLUMNS = {
    "metadata": ("key", "value"),
    "runs": ("id", "agent_snapshot", "adapter_id", "parent_run_id", "completed_context"),
    "turns": ("id", "run_id", "message_id", "input", "context", "submit_seq", "status", "result_text", "error"),
    "delegations": ("child_run_id", "parent_run_id", "parent_turn_id"),
    "message_index": ("run_id", "message_id", "turn_id"),
    "events": ("turn_id", "seq", "run_id", "type", "time", "data"),
}
_SCHEMA = (
    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE runs (id TEXT PRIMARY KEY, agent_snapshot TEXT NOT NULL, adapter_id TEXT NOT NULL, parent_run_id TEXT REFERENCES runs(id), completed_context TEXT NOT NULL)",
    "CREATE TABLE turns (id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), message_id TEXT NOT NULL, input TEXT NOT NULL, context TEXT NOT NULL, submit_seq INTEGER NOT NULL, status TEXT NOT NULL, result_text TEXT, error TEXT, UNIQUE(run_id, message_id), UNIQUE(run_id, submit_seq))",
    "CREATE TABLE delegations (child_run_id TEXT PRIMARY KEY REFERENCES runs(id), parent_run_id TEXT NOT NULL REFERENCES runs(id), parent_turn_id TEXT NOT NULL REFERENCES turns(id))",
    "CREATE TABLE message_index (run_id TEXT NOT NULL REFERENCES runs(id), message_id TEXT NOT NULL, turn_id TEXT NOT NULL UNIQUE REFERENCES turns(id), PRIMARY KEY(run_id, message_id))",
    "CREATE TABLE events (turn_id TEXT NOT NULL REFERENCES turns(id), seq INTEGER NOT NULL, run_id TEXT NOT NULL REFERENCES runs(id), type TEXT NOT NULL, time TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(turn_id, seq))",
)


class _RunStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = root / "runs.sqlite3"
        self._had_store = self.path.exists()
        self._require_empty_root()
        self.connection = _open_store(self.path)
        try:
            self._initialize()
        except RunStoreError:
            self.connection.close()
            raise
        except Exception as error:
            self.connection.close()
            raise RunStoreError(f"runtime store is invalid: {error}") from error

    def _require_empty_root(self):
        if not self._had_store and tuple(self.root.iterdir()):
            raise RunStoreError("runtime store is missing or incomplete")

    def _initialize(self):
        if self._had_store:
            _verify_format(self.connection)
            return
        _create_schema(self.connection)

    def create_run(self, run_id, snapshot, adapter_id, parent_run_id, parent_turn_id):
        if (parent_run_id is None) != (parent_turn_id is None):
            raise RunStoreError("runtime store run parent association is incomplete")
        self._begin()
        try:
            self._insert_run(run_id, snapshot, adapter_id, parent_run_id)
            if parent_turn_id:
                self._insert_delegation(run_id, parent_run_id, parent_turn_id)
            self.connection.commit()
        except (sqlite3.Error, RunStoreError) as error:
            self.connection.rollback()
            raise _store_error(error, "run") from error

    def _insert_run(self, run_id, snapshot, adapter_id, parent_run_id):
        _require_id(run_id, "run id")
        _require_id(adapter_id, "adapter id")
        if parent_run_id is not None:
            _require_id(parent_run_id, "parent run id")
        self.connection.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?)",
            (run_id, _encode(snapshot, "agent snapshot"), adapter_id, parent_run_id, _encode([], "context")),
        )

    def _insert_delegation(self, child_run_id, parent_run_id, parent_turn_id):
        row = self.connection.execute("SELECT run_id FROM turns WHERE id = ?", (parent_turn_id,)).fetchone()
        if row is None or row["run_id"] != parent_run_id:
            raise RunStoreError("runtime store parent turn association is invalid")
        self.connection.execute(
            "INSERT INTO delegations VALUES (?, ?, ?)",
            (child_run_id, parent_run_id, parent_turn_id),
        )

    def create_turn(self, run_id, turn_id, message_id, payload, context, start_event):
        self._begin()
        try:
            submit_seq = self._next_submit_seq(run_id)
            self._insert_turn(run_id, turn_id, message_id, payload, context, submit_seq)
            self.connection.execute(
                "INSERT INTO message_index VALUES (?, ?, ?)", (run_id, message_id, turn_id)
            )
            _insert_event(self.connection, start_event)
            self.connection.commit()
        except (sqlite3.Error, RunStoreError) as error:
            self.connection.rollback()
            raise _store_error(error, "turn") from error
        return submit_seq

    def _next_submit_seq(self, run_id):
        row = self.connection.execute("SELECT MAX(submit_seq) AS value FROM turns WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise RunStoreError(f"runtime store run is missing: {run_id}")
        return (row["value"] if row["value"] is not None else -1) + 1

    def _insert_turn(self, run_id, turn_id, message_id, payload, context, submit_seq):
        _require_id(turn_id, "turn id")
        _require_id(message_id, "message id")
        self.connection.execute(
            "INSERT INTO turns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (turn_id, run_id, message_id, _encode(payload, "message"), _encode(context, "context"), submit_seq, "running", None, None),
        )

    def append_event(self, event):
        self._begin()
        try:
            _insert_event(self.connection, event)
            self.connection.commit()
        except (sqlite3.Error, RunStoreError) as error:
            self.connection.rollback()
            raise _store_error(error, "event") from error

    def next_seq(self, turn_id):
        row = self.connection.execute("SELECT MAX(seq) AS value FROM events WHERE turn_id = ?", (turn_id,)).fetchone()
        if row is None or row["value"] is None:
            raise RunStoreError(f"runtime store turn is missing: {turn_id}")
        return row["value"] + 1

    def finish_turn(self, run_id, turn_id, status, result_text, error, terminal, context, parent_event=None):
        self._begin()
        try:
            if not self._is_running(turn_id):
                self.connection.rollback()
                return ()
            self._update_turn(turn_id, status, result_text, error)
            _insert_event(self.connection, terminal)
            if parent_event:
                _insert_event(self.connection, parent_event)
            self._update_context(run_id, context)
            self.connection.commit()
        except (sqlite3.Error, RunStoreError) as failure:
            self.connection.rollback()
            raise _store_error(failure, "terminal transition") from failure
        return (terminal, parent_event) if parent_event else (terminal,)

    def _is_running(self, turn_id):
        row = self.connection.execute("SELECT status FROM turns WHERE id = ?", (turn_id,)).fetchone()
        if row is None:
            raise RunStoreError(f"runtime store turn is missing: {turn_id}")
        return row["status"] == "running"

    def _update_turn(self, turn_id, status, result_text, error):
        if status not in _STATUSES - {"running"}:
            raise RunStoreError(f"invalid terminal status: {status}")
        self.connection.execute(
            "UPDATE turns SET status = ?, result_text = ?, error = ? WHERE id = ?",
            (status, result_text, error, turn_id),
        )

    def _update_context(self, run_id, context):
        self.connection.execute(
            "UPDATE runs SET completed_context = ? WHERE id = ?",
            (_encode(context, "context"), run_id),
        )

    def has_turn(self, turn_id):
        row = self.connection.execute("SELECT 1 FROM turns WHERE id = ?", (turn_id,)).fetchone()
        return row is not None

    def is_terminal(self, turn_id):
        row = self.connection.execute("SELECT status FROM turns WHERE id = ?", (turn_id,)).fetchone()
        return row is not None and row["status"] != "running"

    def read_events(self, turn_id):
        rows = self.connection.execute("SELECT * FROM events WHERE turn_id = ? ORDER BY seq", (turn_id,))
        return [_event_row(row) for row in rows]

    def snapshot(self):
        try:
            value = _load_snapshot(self.connection)
            _validate_snapshot(value)
            return value
        except RunStoreError:
            raise
        except (sqlite3.Error, ValueError, TypeError, KeyError) as error:
            raise RunStoreError(f"runtime store is invalid: {error}") from error

    def _begin(self):
        try:
            self.connection.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as error:
            raise RunStoreError(f"runtime store transaction failed: {error}") from error


def _connect(path):
    connection = sqlite3.connect(path, timeout=5, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


def _open_store(path):
    try:
        return _connect(path)
    except (OSError, sqlite3.Error) as error:
        raise RunStoreError(f"runtime store is invalid: {error}") from error


def _create_schema(connection):
    with _transaction(connection):
        for statement in _SCHEMA:
            connection.execute(statement)
        for key, value in _FORMAT.items():
            connection.execute("INSERT INTO metadata VALUES (?, ?)", (key, value))


def _verify_format(connection):
    _verify_metadata(connection)
    names = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")}
    if names != set(_TABLE_COLUMNS):
        raise RunStoreError("runtime store has an unknown schema")
    for table, columns in _TABLE_COLUMNS.items():
        _verify_columns(connection, table, columns)
    _verify_schema(connection)
    _verify_integrity(connection)
    if tuple(connection.execute("PRAGMA foreign_key_check")):
        raise RunStoreError("runtime store has incomplete associations")


def _verify_metadata(connection):
    rows = connection.execute("SELECT key, value FROM metadata").fetchall()
    if {row["key"]: row["value"] for row in rows} != _FORMAT:
        raise RunStoreError("runtime store has an unknown format")


def _verify_columns(connection, table, expected):
    actual = tuple(row["name"] for row in connection.execute(f"PRAGMA table_info({table})"))
    if actual != expected:
        raise RunStoreError(f"runtime store has an invalid {table} schema")


def _verify_schema(connection):
    objects = connection.execute("SELECT type, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    actual = {row["sql"] for row in objects if row["type"] == "table"}
    if any(row["type"] != "table" for row in objects) or actual != set(_SCHEMA):
        raise RunStoreError("runtime store has invalid schema constraints")


def _verify_integrity(connection):
    result = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if result != ["ok"]:
        raise RunStoreError("runtime store failed integrity check")


@contextmanager
def _transaction(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        connection.rollback()
        raise
    connection.commit()


def _insert_event(connection, event):
    fields = _event_fields(event)
    connection.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        (*fields[:4], fields[4], _encode(fields[5], "event data")),
    )


def _event_fields(event):
    if not isinstance(event, dict) or set(event) != {"run_id", "turn_id", "seq", "type", "time", "data"}:
        raise RunStoreError("runtime event has an invalid shape")
    _require_id(event["run_id"], "event run id")
    _require_id(event["turn_id"], "event turn id")
    if not isinstance(event["seq"], int) or isinstance(event["seq"], bool) or event["seq"] < 0:
        raise RunStoreError("runtime event sequence is invalid")
    if not isinstance(event["type"], str) or not event["type"]:
        raise RunStoreError("runtime event type is invalid")
    if not isinstance(event["time"], str) or not event["time"]:
        raise RunStoreError("runtime event time is invalid")
    if not isinstance(event["data"], dict):
        raise RunStoreError("runtime event data is invalid")
    return event["turn_id"], event["seq"], event["run_id"], event["type"], event["time"], event["data"]


def _load_snapshot(connection):
    return {
        "runs": _rows(connection, "SELECT * FROM runs", _run_row),
        "turns": _rows(connection, "SELECT * FROM turns", _turn_row),
        "delegations": _delegation_rows(connection),
        "messages": _message_rows(connection),
        "events": _event_rows(connection),
    }


def _rows(connection, query, decoder):
    result = {}
    for row in connection.execute(query):
        value = decoder(row)
        _put_unique(result, value["id"], value, "record")
    return result


def _message_rows(connection):
    result = {}
    for row in connection.execute("SELECT * FROM message_index"):
        run = result.setdefault(row["run_id"], {})
        _put_unique(run, row["message_id"], row["turn_id"], "message")
    return result


def _delegation_rows(connection):
    result = {}
    for row in connection.execute("SELECT * FROM delegations"):
        value = _delegation_row(row)
        _put_unique(result, value["child_run_id"], value, "delegation")
    return result


def _event_rows(connection):
    result = {}
    for row in connection.execute("SELECT * FROM events ORDER BY turn_id, seq"):
        result.setdefault(row["turn_id"], []).append(_event_row(row))
    return result


def _run_row(row):
    return {"id": row["id"], "agent_snapshot": _decode(row["agent_snapshot"], "agent snapshot"), "adapter_id": row["adapter_id"], "parent_run_id": row["parent_run_id"], "context": _decode(row["completed_context"], "context")}


def _turn_row(row):
    return {"id": row["id"], "run_id": row["run_id"], "message_id": row["message_id"], "input": _decode(row["input"], "message"), "context": _decode(row["context"], "context"), "submit_seq": row["submit_seq"], "status": row["status"], "result_text": row["result_text"], "error": row["error"]}


def _delegation_row(row):
    return {"child_run_id": row["child_run_id"], "parent_run_id": row["parent_run_id"], "parent_turn_id": row["parent_turn_id"]}


def _event_row(row):
    return {"run_id": row["run_id"], "turn_id": row["turn_id"], "seq": row["seq"], "type": row["type"], "time": row["time"], "data": _decode(row["data"], "event data")}


def _validate_snapshot(value):
    _validate_runs(value)
    _validate_turns(value)
    _validate_submit_sequences(value)
    _validate_delegations(value)
    _validate_messages(value)
    _validate_events(value)
    _validate_contexts(value)


def _validate_runs(value):
    runs = value["runs"]
    if not isinstance(runs, dict):
        raise RunStoreError("runtime store runs are invalid")
    for run_id, run in runs.items():
        _validate_run(run_id, run, runs)


def _validate_run(run_id, run, runs):
    _require_id(run_id, "run id")
    if not isinstance(run, dict) or run.get("id") != run_id:
        raise RunStoreError("runtime store run identity is invalid")
    if not isinstance(run.get("adapter_id"), str) or not run["adapter_id"]:
        raise RunStoreError("runtime store adapter id is invalid")
    if not isinstance(run.get("agent_snapshot"), dict) or run["agent_snapshot"].get("adapter") != run.get("adapter_id"):
        raise RunStoreError("runtime store adapter binding is invalid")
    _validate_snapshot_fields(run["agent_snapshot"])
    parent_id = run.get("parent_run_id")
    if parent_id is not None and (not isinstance(parent_id, str) or parent_id not in runs):
        raise RunStoreError("runtime store parent run association is invalid")
    _validate_context_value(run.get("context"))


def _validate_turns(value):
    turns = value["turns"]
    if not isinstance(turns, dict):
        raise RunStoreError("runtime store turns are invalid")
    for turn_id, turn in turns.items():
        _validate_turn(turn_id, turn, value["runs"])


def _validate_turn(turn_id, turn, runs):
    if not isinstance(turn, dict) or turn.get("id") != turn_id or turn.get("run_id") not in runs:
        raise RunStoreError("runtime store turn association is invalid")
    _require_id(turn.get("message_id"), "message id")
    if not isinstance(turn.get("submit_seq"), int) or isinstance(turn["submit_seq"], bool) or turn["submit_seq"] < 0:
        raise RunStoreError("runtime store submit order is invalid")
    if turn.get("status") not in _STATUSES:
        raise RunStoreError("runtime store turn state is invalid")
    _validate_context_value(turn.get("context"))
    if turn.get("result_text") is not None and not isinstance(turn["result_text"], str):
        raise RunStoreError("runtime store result is invalid")
    if turn.get("error") is not None and not isinstance(turn["error"], str):
        raise RunStoreError("runtime store error is invalid")


def _validate_submit_sequences(value):
    sequences = {}
    for turn in value["turns"].values():
        sequences.setdefault(turn["run_id"], []).append(turn["submit_seq"])
    for values in sequences.values():
        if sorted(values) != list(range(len(values))):
            raise RunStoreError("runtime store submit order is not contiguous")


def _validate_delegations(value):
    for child_id, link in value["delegations"].items():
        if not isinstance(link, dict) or child_id == link.get("parent_run_id"):
            raise RunStoreError("runtime store delegation identity is invalid")
        if child_id not in value["runs"] or link["parent_run_id"] not in value["runs"]:
            raise RunStoreError("runtime store delegation run is invalid")
        parent = value["turns"].get(link["parent_turn_id"])
        if parent is None or parent["run_id"] != link["parent_run_id"]:
            raise RunStoreError("runtime store delegation turn is invalid")
        if value["runs"][child_id]["parent_run_id"] != link["parent_run_id"]:
            raise RunStoreError("runtime store delegation parent is inconsistent")
    for run_id, run in value["runs"].items():
        has_parent = run["parent_run_id"] is not None
        if has_parent != (run_id in value["delegations"]):
            raise RunStoreError("runtime store delegation association is incomplete")
    _validate_acyclic_runs(value["runs"])


def _validate_acyclic_runs(runs):
    for start in runs:
        seen = set()
        current = start
        while current is not None:
            if current in seen:
                raise RunStoreError("runtime store delegation graph is cyclic")
            seen.add(current)
            current = runs[current]["parent_run_id"]


def _validate_messages(value):
    expected = {}
    for turn in value["turns"].values():
        _put_unique(expected, (turn["run_id"], turn["message_id"]), turn["id"], "message")
    actual = {(run_id, message_id): turn_id for run_id, messages in value["messages"].items() for message_id, turn_id in messages.items()}
    if actual != expected:
        raise RunStoreError("runtime store message index is inconsistent")


def _validate_events(value):
    if not isinstance(value["events"], dict):
        raise RunStoreError("runtime store events are invalid")
    if set(value["events"]) != set(value["turns"]):
        raise RunStoreError("runtime store event index is incomplete")
    for turn_id, events in value["events"].items():
        turn = value["turns"].get(turn_id)
        if turn is None:
            raise RunStoreError("runtime store event turn is invalid")
        _validate_event_sequence(turn, events, value["runs"])
    _validate_child_result_events(value)
    _validate_required_child_results(value)


def _validate_event_sequence(turn, events, runs):
    if not events or events[0]["type"] != "turn_start":
        raise RunStoreError("runtime store turn start is missing")
    for seq, event in enumerate(events):
        _validate_event(event, turn, seq, runs)
    ends = [event for event in events if event["type"] == "turn_end"]
    if turn["status"] == "running" and ends:
        raise RunStoreError("runtime store running turn is terminal")
    if turn["status"] != "running" and (len(ends) != 1 or ends[0] is not events[-1]):
        raise RunStoreError("runtime store terminal event is inconsistent")
    _validate_start(turn, events[0])
    if ends:
        _validate_end(turn, ends[0])


def _validate_event(event, turn, seq, runs):
    if not isinstance(event.get("seq"), int) or event["seq"] != seq:
        raise RunStoreError("runtime store event sequence is invalid")
    if event["turn_id"] != turn["id"] or event["run_id"] != runs[turn["run_id"]]["id"]:
        raise RunStoreError("runtime store event association is invalid")
    if not isinstance(event.get("type"), str) or not event["type"]:
        raise RunStoreError("runtime store event type is invalid")
    if not isinstance(event["time"], str) or not event["time"] or not isinstance(event["data"], dict):
        raise RunStoreError("runtime store event is invalid")


def _validate_child_result_events(value):
    for events in value["events"].values():
        for event in events:
            if event["type"] == "child_result":
                _validate_child_result_event(event, value)


def _validate_child_result_event(event, value):
    data = event["data"]
    allowed = {"child_run_id", "child_turn_id", "status", "result_text", "error"}
    child = value["turns"].get(data.get("child_turn_id"))
    link = value["delegations"].get(data.get("child_run_id"))
    if set(data) - allowed or not {"child_run_id", "child_turn_id", "status", "result_text"} <= set(data):
        raise RunStoreError("runtime store child result shape is invalid")
    if child is None or link is None or child["run_id"] != data["child_run_id"] or link["parent_turn_id"] != event["turn_id"]:
        raise RunStoreError("runtime store child result association is invalid")
    if child["status"] == "running" or data["status"] != child["status"] or data["result_text"] != child["result_text"]:
        raise RunStoreError("runtime store child result is inconsistent")
    if (child["error"] is None) != ("error" not in data) or data.get("error") != child["error"]:
        raise RunStoreError("runtime store child result error is inconsistent")


def _validate_required_child_results(value):
    for child_id, link in value["delegations"].items():
        parent = value["turns"][link["parent_turn_id"]]
        if parent["status"] not in {"running", "completed", "limit"}:
            continue
        children = [turn for turn in value["turns"].values() if turn["run_id"] == child_id and turn["status"] != "running"]
        for child in children:
            matches = [event for event in value["events"][parent["id"]] if event["type"] == "child_result" and event["data"]["child_turn_id"] == child["id"]]
            if len(matches) != 1:
                raise RunStoreError("runtime store child result association is incomplete")


def _validate_start(turn, event):
    if set(event["data"]) != {"message_id", "input"} or event["data"] != {"message_id": turn["message_id"], "input": turn["input"]}:
        raise RunStoreError("runtime store turn start is inconsistent")


def _validate_end(turn, event):
    data = event["data"]
    if set(data) - {"status", "result_text", "error"} or not {"status", "result_text"} <= set(data):
        raise RunStoreError("runtime store turn end shape is invalid")
    if data.get("status") != turn["status"] or data.get("result_text") != turn["result_text"]:
        raise RunStoreError("runtime store turn end is inconsistent")
    if (turn["error"] is None) != ("error" not in data) or data.get("error") != turn["error"]:
        raise RunStoreError("runtime store turn error is inconsistent")


def _validate_contexts(value):
    for run_id, run in value["runs"].items():
        turns = [turn for turn in value["turns"].values() if turn["run_id"] == run_id]
        expected = _completed_context(sorted(turns, key=lambda item: item["submit_seq"]))
        if run["context"] != expected:
            raise RunStoreError("runtime store completed context is inconsistent")


def _completed_context(turns):
    context = []
    for turn in turns:
        if turn["status"] in {"completed", "limit"}:
            context.extend(_context_entry(turn["message_id"], turn["input"], turn["result_text"]))
    return context


def _context_entry(message_id, payload, result_text):
    return [{"role": "user", "message_id": message_id, "content": payload}, {"role": "assistant", "content": result_text or ""}]


def _validate_context_value(value):
    if not isinstance(value, list) or len(value) % 2 or any(not isinstance(item, dict) for item in value):
        raise RunStoreError("runtime store context is invalid")
    for index in range(0, len(value), 2):
        _validate_context_pair(value[index:index + 2])


def _validate_context_pair(pair):
    if set(pair[0]) != {"role", "message_id", "content"} or pair[0]["role"] != "user" or not isinstance(pair[0]["message_id"], str):
        raise RunStoreError("runtime store user context is invalid")
    if set(pair[1]) != {"role", "content"} or pair[1]["role"] != "assistant" or not isinstance(pair[1]["content"], str):
        raise RunStoreError("runtime store assistant context is invalid")


def _validate_snapshot_fields(value):
    unknown = tuple(key for key in value) if not isinstance(value, dict) else tuple(key for key in value if key not in _AGENT_SPEC_FIELDS)
    if unknown:
        raise RunStoreError(f"runtime store agent snapshot contains unsupported fields: {unknown}")
    if not isinstance(value, dict):
        raise RunStoreError("runtime store agent snapshot is invalid")
    if any(key in value and not isinstance(value[key], str) for key in _AGENT_TEXT_FIELDS):
        raise RunStoreError("runtime store agent snapshot contains invalid fields")
    tools = value.get("tools", [])
    if not isinstance(tools, list) or any(not isinstance(tool, str) for tool in tools):
        raise RunStoreError("runtime store agent snapshot contains invalid tools")
    params = value.get("params", {})
    if not isinstance(params, dict) or any(key not in _AGENT_PARAMS_FIELDS for key in params):
        raise RunStoreError("runtime store agent snapshot contains invalid params")
    if "mode" in params and not isinstance(params["mode"], str):
        raise RunStoreError("runtime store agent snapshot contains invalid params")


def _put_unique(mapping, key, value, label):
    if key in mapping:
        raise RunStoreError(f"runtime store duplicate {label} id")
    mapping[key] = value


def _require_id(value, label):
    if not isinstance(value, str) or not value:
        raise RunStoreError(f"runtime store {label} is invalid")


def _encode(value, label):
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise RunStoreError(f"runtime store cannot encode {label}: {error}") from error


def _decode(value, label):
    try:
        return json.loads(value, parse_constant=_invalid_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise RunStoreError(f"runtime store cannot decode {label}: {error}") from error


def _invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def _store_error(error, operation):
    if isinstance(error, RunStoreError):
        return error
    return RunStoreError(f"runtime store {operation} failed: {error}")

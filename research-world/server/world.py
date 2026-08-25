from __future__ import annotations

import json
import secrets
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .admission import AdmissionVerdict
from .artifacts import now
from .db import Database
from .library import assembly_names
from .titles import validate_title

NODE_KINDS = {"question", "source", "direction", "experiment"}
LIFE_STATES = {"pending", "admitted", "ghost"}
EDGE_POLARITIES = {"supports", "refutes"}
DIRECTION_STATES = {"proposed", "supported", "refuted"}
RUN_LEASE_SECONDS = 30


def decode(row: sqlite3.Row) -> dict:
    value = dict(row)
    for key in ("payload", "rebuttal", "output", "assembly", "definition_snapshot"):
        if value.get(key):
            value[key] = json.loads(value[key])
    return value


def node_text(payload: dict) -> str:
    return " ".join(
        str(payload.get(key, ""))
        for key in ("title", "text", "summary")
        if payload.get(key)
    )


class World:
    def __init__(
        self, database: Path, artifacts: Path, embedding: Callable | None = None
    ):
        self.db = Database(database)
        self.artifacts_root = artifacts
        self.embedding = embedding

    def create_project(
        self, name: str, root: Path, title: str, question: str, assembly: list[str] | None = None
    ) -> dict:
        title = validate_title(title)
        project_id = f"project:{secrets.token_hex(12)}"
        names = json.dumps(assembly_names(assembly))
        values = (project_id, name, str(root.resolve()), question, 0, names, now())
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO projects(id,name,root,question,auto,assembly,created_at) VALUES(?,?,?,?,?,?,?)",
                values,
            )
            self._insert_question(connection, project_id, title, question)
        return self.project(project_id)

    def _insert_question(self, connection, project_id: str, title: str, text: str) -> None:
        node_id = f"node:{secrets.token_hex(12)}"
        values = question_values(node_id, project_id, title, text)
        connection.execute(
            "INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", values
        )
        connection.execute(
            "INSERT INTO node_fts VALUES(?,?,?)", (node_id, project_id, text)
        )

    def project(self, project_id: str) -> dict:
        return self._one("SELECT * FROM projects WHERE id=?", (project_id,))

    def project_by_name(self, name: str) -> dict:
        return self._one("SELECT * FROM projects WHERE name=?", (name,))

    def projects(self) -> list[dict]:
        return self._many("SELECT * FROM projects ORDER BY created_at")

    def set_auto(self, project_id: str, enabled: bool) -> dict:
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE projects SET auto=? WHERE id=?", (int(enabled), project_id)
            )
        return self.project(project_id)

    def create_node(self, project_id: str, kind: str, payload: dict, **state) -> dict:
        self._validate_node(
            kind, state.get("life_state", "pending"), state.get("direction_status")
        )
        payload = {**payload, "title": validate_title(payload.get("title"))}
        node_id = f"node:{secrets.token_hex(12)}"
        parent_id = state.get("parent_id")
        lineage_id = state.get("lineage_id") or self._lineage(parent_id, node_id)
        values = self._node_values(
            node_id, project_id, kind, payload, lineage_id, state
        )
        self._write_node(project_id, node_id, lineage_id, payload, values)
        return self.node(node_id)

    def _write_node(self, project_id, node_id, lineage_id, payload, values) -> None:
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", values
            )
            connection.execute(
                "INSERT OR IGNORE INTO lineages VALUES(?,?,0,0)",
                (lineage_id, project_id),
            )
            connection.execute(
                "INSERT INTO node_fts VALUES(?,?,?)",
                (node_id, project_id, node_text(payload)),
            )
            self._store_embedding(connection, node_id, payload)

    def _node_values(
        self, node_id, project_id, kind, payload, lineage_id, state
    ) -> tuple:
        direction_status = node_direction_status(kind, state)
        return (
            node_id,
            project_id,
            state.get("parent_id"),
            lineage_id,
            kind,
            json.dumps(payload),
            state.get("life_state", "pending"),
            direction_status,
            int(state.get("working", False)),
            state.get("rejection_reason"),
            json.dumps(state["rebuttal"]) if state.get("rebuttal") else None,
            now(),
            now(),
        )

    def _validate_node(
        self, kind: str, life_state: str, direction_status: str | None
    ) -> None:
        if kind not in NODE_KINDS or life_state not in LIFE_STATES:
            raise ValueError("invalid node kind or life state")
        if kind != "direction" and direction_status is not None:
            raise ValueError("only direction nodes have direction status")
        if direction_status is not None and direction_status not in DIRECTION_STATES:
            raise ValueError("invalid direction status")

    def _lineage(self, parent_id: str | None, fallback: str) -> str:
        return self.node(parent_id)["lineage_id"] if parent_id else fallback

    def node(self, node_id: str) -> dict:
        return self._one("SELECT * FROM nodes WHERE id=?", (node_id,))

    def nodes(self, project_id: str) -> list[dict]:
        return self._many(
            "SELECT * FROM nodes WHERE project_id=? ORDER BY created_at", (project_id,)
        )

    def update_node(self, node_id: str, payload: dict | None = None, **state) -> dict:
        node = self.node(node_id)
        self._validate_transition(node, state)
        fields = self._node_updates(node, payload, state)
        assignments = ",".join(f"{key}=?" for key in fields)
        with self.db.connect() as connection:
            connection.execute(
                f"UPDATE nodes SET {assignments} WHERE id=?",
                (*fields.values(), node_id),
            )
        return self.node(node_id)

    def _validate_transition(self, node: dict, state: dict) -> None:
        target = state.get("direction_status")
        if target and node["kind"] != "direction":
            raise ValueError("only direction nodes have direction status")
        if target and node["direction_status"] != "proposed":
            raise ValueError("direction status is terminal")
        if target and target not in {"supported", "refuted"}:
            raise ValueError("direction must resolve to supported or refuted")

    def _node_updates(self, node: dict, payload: dict | None, state: dict) -> dict:
        fields = {
            key: state[key]
            for key in ("life_state", "direction_status", "rejection_reason")
            if key in state
        }
        if payload is not None:
            fields["payload"] = json.dumps(payload)
        if "working" in state:
            fields["working"] = int(state["working"])
        if "rebuttal" in state:
            fields["rebuttal"] = json.dumps(state["rebuttal"])
        fields["updated_at"] = now()
        return fields

    def admit_node(self, node_id: str, payload: dict | None = None) -> dict:
        return self.update_node(
            node_id,
            payload,
            life_state="admitted",
            working=False,
            rejection_reason=None,
        )

    def ghost_node(
        self, node_id: str, reason: str, rebuttal: dict | None = None
    ) -> dict:
        if not reason.strip():
            raise ValueError("ghost node requires a rejection reason")
        return self.update_node(
            node_id,
            life_state="ghost",
            working=False,
            rejection_reason=reason.strip(),
            rebuttal=rebuttal,
        )

    def apply_admission(self, node_id: str, verdict: AdmissionVerdict) -> dict:
        if not isinstance(verdict, AdmissionVerdict):
            raise TypeError("admission requires an AdmissionVerdict")
        return self._apply_pending_admission(node_id, verdict)

    def _apply_pending_admission(self, node_id, verdict) -> dict:
        life_state = "admitted" if verdict.decision == "approve" else "ghost"
        rejection = None if verdict.decision == "approve" else verdict.reason.strip()
        encoded = json.dumps(verdict.rebuttal) if verdict.rebuttal is not None else None
        with self.db.connect() as connection:
            cursor = connection.execute(
                "UPDATE nodes SET life_state=?,working=0,rejection_reason=?,rebuttal=?,updated_at=? "
                "WHERE id=? AND life_state='pending'",
                (life_state, rejection, encoded, now(), node_id),
            )
        if cursor.rowcount != 1:
            self.node(node_id)
            raise ValueError("only pending nodes can receive an admission verdict")
        return self.node(node_id)

    def set_working(self, node_id: str, working: bool) -> dict:
        return self.update_node(node_id, working=working)

    def add_edge(self, source: str, target: str, polarity: str) -> dict:
        if polarity not in EDGE_POLARITIES:
            raise ValueError("edge polarity must be supports or refutes")
        self._validate_edge_nodes(source, target)
        values = (source, target, polarity, now())
        with self.db.connect() as connection:
            connection.execute("INSERT INTO edges VALUES(?,?,?,?)", values)
        return {"source": source, "target": target, "polarity": polarity}

    def _validate_edge_nodes(self, source: str, target: str) -> None:
        left, right = self.node(source), self.node(target)
        if left["project_id"] != right["project_id"]:
            raise ValueError("edge nodes must belong to one project")

    def edges(self, project_id: str) -> list[dict]:
        sql = "SELECT e.* FROM edges e JOIN nodes n ON n.id=e.source WHERE n.project_id=? ORDER BY e.created_at"
        return self._many(sql, (project_id,))

    def search(self, project_id: str, query: str) -> list[dict]:
        terms = " OR ".join(part for part in query.split() if part)
        if not terms:
            return []
        sql = "SELECT n.* FROM node_fts f JOIN nodes n ON n.id=f.node_id WHERE f.project_id=? AND node_fts MATCH ?"
        return self._many(sql, (project_id, terms))

    def _store_embedding(self, connection, node_id: str, payload: dict) -> None:
        if self.embedding is None:
            return
        vector = self.embedding(node_text(payload))
        connection.execute(
            "INSERT INTO node_embeddings VALUES(?,?)", (node_id, json.dumps(vector))
        )

    def embedding_for(self, node_id: str) -> list[float] | None:
        rows = self._rows(
            "SELECT vector FROM node_embeddings WHERE node_id=?", (node_id,)
        )
        return json.loads(rows[0]["vector"]) if rows else None

    def create_thread(
        self, project_id: str, title: str, session_id: str, agent_id: str
    ) -> dict:
        self.project(project_id)
        thread_id = f"thread:{secrets.token_hex(12)}"
        timestamp = now()
        values = (
            thread_id,
            project_id,
            title.strip() or "新对话",
            session_id,
            agent_id,
            0,
            timestamp,
            timestamp,
        )
        with self.db.connect() as connection:
            connection.execute("INSERT INTO threads VALUES(?,?,?,?,?,?,?,?)", values)
        return self.thread(thread_id)

    def thread(self, thread_id: str) -> dict:
        value = self._one("SELECT * FROM threads WHERE id=?", (thread_id,))
        value["nodes"] = self.thread_nodes(thread_id)
        return value

    def threads(self, project_id: str) -> list[dict]:
        rows = self._many(
            "SELECT * FROM threads WHERE project_id=? AND archived=0 ORDER BY updated_at DESC",
            (project_id,),
        )
        for item in rows:
            item["nodes"] = self.thread_nodes(item["id"])
        return rows

    def update_thread_session(self, thread_id: str, session_id: str) -> dict:
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE threads SET session_id=?,updated_at=? WHERE id=?",
                (session_id, now(), thread_id),
            )
        return self.thread(thread_id)

    def touch_thread(self, thread_id: str) -> None:
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE threads SET updated_at=? WHERE id=?", (now(), thread_id)
            )

    def pin_thread_node(self, thread_id: str, node_id: str) -> dict:
        self._validate_thread_node(thread_id, node_id)
        with self.db.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO thread_nodes VALUES(?,?,?)",
                (thread_id, node_id, now()),
            )
        return self.thread(thread_id)

    def unpin_thread_node(self, thread_id: str, node_id: str) -> dict:
        self._validate_thread_node(thread_id, node_id)
        with self.db.connect() as connection:
            connection.execute(
                "DELETE FROM thread_nodes WHERE thread_id=? AND node_id=?",
                (thread_id, node_id),
            )
        return self.thread(thread_id)

    def thread_nodes(self, thread_id: str) -> list[dict]:
        sql = "SELECT n.* FROM thread_nodes t JOIN nodes n ON n.id=t.node_id WHERE t.thread_id=? ORDER BY t.pinned_at"
        return self._many(sql, (thread_id,))

    def _validate_thread_node(self, thread_id: str, node_id: str) -> None:
        thread, node = self.thread(thread_id), self.node(node_id)
        if thread["project_id"] != node["project_id"]:
            raise ValueError("thread node belongs to another project")

    def active_run(self, project_id: str, node_id: str) -> dict | None:
        active = [
            item
            for item in self.runs(project_id)
            if item["status"] in {"queued", "running", "waiting_human"}
        ]
        associated = next(
            (
                item
                for item in active
                if item["payload"].get("experiment_id") == node_id
            ),
            None,
        )
        return associated or next(
            (item for item in active if item["node_id"] == node_id), None
        )

    def create_run(
        self, project_id: str, node_id: str, pipeline: dict, payload: dict | None = None
    ) -> dict:
        project, node = self.project(project_id), self.node(node_id)
        if node["project_id"] != project_id:
            raise ValueError("pipeline node belongs to another project")
        if active := self.active_run(project_id, node_id):
            return active
        run_id = f"run:{secrets.token_hex(12)}"
        values = run_values(run_id, project, node, pipeline, payload)
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO pipeline_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", values
            )
            connection.execute(
                "INSERT OR IGNORE INTO lineages VALUES(?,?,0,0)",
                (node["lineage_id"], project_id),
            )
        return self.run(run_id)

    def run(self, run_id: str) -> dict:
        return self._one("SELECT * FROM pipeline_runs WHERE id=?", (run_id,))

    def runs(self, project_id: str | None = None) -> list[dict]:
        sql = (
            "SELECT * FROM pipeline_runs"
            + (" WHERE project_id=?" if project_id else "")
            + " ORDER BY created_at DESC"
        )
        return self._many(sql, (project_id,) if project_id else ())

    def claim_run(self) -> dict | None:
        sql = """UPDATE pipeline_runs SET status='running',updated_at=? WHERE id=(
        SELECT id FROM pipeline_runs WHERE status='queued' OR
        (status='running' AND updated_at<?)
        ORDER BY CASE status WHEN 'queued' THEN 0 ELSE 1 END,created_at LIMIT 1
        ) RETURNING *"""
        timestamp = now()
        expired = (datetime.now(UTC) - timedelta(seconds=RUN_LEASE_SECONDS)).isoformat()
        with self.db.connect() as connection:
            row = connection.execute(sql, (timestamp, expired)).fetchone()
        return decode(row) if row else None

    def touch_run(self, run_id: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.execute(
                "UPDATE pipeline_runs SET updated_at=? WHERE id=? AND status='running'",
                (now(), run_id),
            )
        return cursor.rowcount == 1

    def update_run(
        self, run_id: str, stage: str, status: str, payload: dict | None = None
    ) -> dict:
        current = self.run(run_id)
        value = payload if payload is not None else current["payload"]
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE pipeline_runs SET stage=?,status=?,payload=?,updated_at=? WHERE id=?",
                (stage, status, json.dumps(value), now(), run_id),
            )
        return self.run(run_id)

    def transition_run(
        self, run_id: str, stage: str, status: str, payload: dict, event: dict
    ) -> dict:
        timestamp = now()
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE pipeline_runs SET stage=?,status=?,payload=?,updated_at=? WHERE id=?",
                (stage, status, json.dumps(payload), timestamp, run_id),
            )
            _append_run_event(connection, run_id, event, timestamp)
        return self.run(run_id)

    def queue_run_signal(self, run_id: str, signal: dict) -> dict:
        run = self.run(run_id)
        gate = run["payload"].get("_pipeline", {}).get("gate")
        if run["status"] != "waiting_human" or not gate:
            raise ValueError("run has no human gate")
        _validate_run_signal(gate, signal)
        payload = {**run["payload"], "_signal": signal}
        return self._queue_run_signal(run_id, payload, signal)

    def _queue_run_signal(self, run_id: str, payload: dict, signal: dict) -> dict:
        timestamp = now()
        with self.db.connect() as connection:
            cursor = connection.execute(
                "UPDATE pipeline_runs SET status='queued',payload=?,updated_at=? "
                "WHERE id=? AND status='waiting_human'",
                (json.dumps(payload), timestamp, run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("human gate was already resolved")
            connection.execute(
                "INSERT INTO pipeline_events(run_id,actor,type,payload,time) VALUES(?,?,?,?,?)",
                (run_id, "human", "gate_resolved", json.dumps(signal), timestamp),
            )
        return self.run(run_id)

    def add_step(
        self, run_id: str, ordinal: int, stage: str, payload: dict, confirm: bool
    ) -> dict:
        step_id = f"step:{secrets.token_hex(12)}"
        values = step_values(step_id, run_id, ordinal, stage, payload, confirm)
        with self.db.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO pipeline_steps VALUES(?,?,?,?,?,?,?,?,?,?)",
                values,
            )
        return self._one(
            "SELECT * FROM pipeline_steps WHERE run_id=? AND ordinal=?",
            (run_id, ordinal),
        )

    def steps(self, run_id: str) -> list[dict]:
        return self._many(
            "SELECT * FROM pipeline_steps WHERE run_id=? ORDER BY ordinal", (run_id,)
        )

    def update_step(
        self, step_id: str, status: str, output: dict | None = None
    ) -> dict:
        started = now() if status == "running" else None
        completed = now() if status in {"completed", "failed"} else None
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE pipeline_steps SET status=?,output=COALESCE(?,output),started_at=COALESCE(?,started_at),completed_at=COALESCE(?,completed_at) WHERE id=?",
                (
                    status,
                    json.dumps(output) if output is not None else None,
                    started,
                    completed,
                    step_id,
                ),
            )
        return self._one("SELECT * FROM pipeline_steps WHERE id=?", (step_id,))

    def record_run_event(
        self, run_id: str, actor: str, event_type: str, payload: dict
    ) -> dict:
        values = (run_id, actor, event_type, json.dumps(payload), now())
        with self.db.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO pipeline_events(run_id,actor,type,payload,time) VALUES(?,?,?,?,?)",
                values,
            )
        return self._one(
            "SELECT * FROM pipeline_events WHERE id=?", (cursor.lastrowid,)
        )

    def run_events(self, run_id: str) -> list[dict]:
        return self._many(
            "SELECT * FROM pipeline_events WHERE run_id=? ORDER BY id", (run_id,)
        )

    def resolve_direction_review(
        self, node_id: str, approved: bool, reason: str
    ) -> dict:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM nodes WHERE id=?", (node_id,)
            ).fetchone()
            node = decode(row)
            changed = node["life_state"] == "pending"
            if changed:
                _resolve_node(connection, node, approved, reason)
                lineage = _register_review(connection, node["lineage_id"], approved)
            else:
                lineage = _lineage(connection, node["lineage_id"])
        return {"changed": changed, "node": self.node(node_id), "lineage": lineage}

    def resolve_experiment_review(
        self, experiment_id: str, direction_id: str, approved: bool, payload: dict
    ) -> dict:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM nodes WHERE id=?", (experiment_id,)
            ).fetchone()
            experiment = decode(row)
            changed = experiment["life_state"] == "pending"
            if changed:
                _resolve_experiment(
                    connection, experiment, direction_id, approved, payload
                )
            lineage = _lineage(connection, experiment["lineage_id"])
        return {"changed": changed, "lineage": lineage}

    def _rows(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.db.connect() as connection:
            return connection.execute(sql, params).fetchall()

    def _one(self, sql: str, params: tuple = ()) -> dict:
        rows = self._rows(sql, params)
        if not rows:
            raise KeyError(params[0] if params else sql)
        return decode(rows[0])

    def _many(self, sql: str, params: tuple = ()) -> list[dict]:
        return [decode(row) for row in self._rows(sql, params)]


def question_values(node_id: str, project_id: str, title: str, text: str) -> tuple:
    timestamp = now()
    return (
        node_id,
        project_id,
        None,
        node_id,
        "question",
        json.dumps({"title": validate_title(title), "text": text}),
        "admitted",
        None,
        0,
        None,
        None,
        timestamp,
        timestamp,
    )


def node_direction_status(kind: str, state: dict) -> str | None:
    return state.get("direction_status") or (
        "proposed" if kind == "direction" else None
    )


def run_values(run_id, project, node, pipeline, payload) -> tuple:
    timestamp = now()
    return (
        run_id,
        project["id"],
        node["id"],
        node["lineage_id"],
        pipeline["id"],
        json.dumps(pipeline),
        "created",
        "queued",
        json.dumps(payload or {}),
        project["auto"],
        timestamp,
        timestamp,
    )


def step_values(step_id, run_id, ordinal, stage, payload, confirm) -> tuple:
    return (
        step_id,
        run_id,
        ordinal,
        stage,
        "pending",
        int(confirm),
        json.dumps(payload),
        None,
        None,
        None,
    )


def _append_run_event(connection, run_id, event, timestamp) -> None:
    connection.execute(
        "INSERT INTO pipeline_events(run_id,actor,type,payload,time) VALUES(?,?,?,?,?)",
        (
            run_id,
            event["actor"],
            event["type"],
            json.dumps(event["payload"]),
            timestamp,
        ),
    )


def _validate_run_signal(gate: dict, signal: dict) -> None:
    if signal.get("kind") != gate.get("kind"):
        raise ValueError("signal does not match human gate")
    decision = signal.get("decision")
    if gate["kind"] == "confirm_step" and decision not in {None, "reject"}:
        raise ValueError("execution gate only accepts rejection")
    if gate["kind"] == "review" and decision not in {"approve", "reject"}:
        raise ValueError("review gate requires approve or reject")
    if decision and not str(signal.get("reason", "")).strip():
        raise ValueError("human gate decision requires a reason")


def _resolve_node(connection, node, approved, reason) -> None:
    life_state = "admitted" if approved else "ghost"
    rejection = None if approved else reason.strip()
    connection.execute(
        "UPDATE nodes SET life_state=?,working=0,rejection_reason=?,updated_at=? WHERE id=?",
        (life_state, rejection, now(), node["id"]),
    )


def _resolve_experiment(connection, experiment, direction_id, approved, payload):
    _resolve_node(connection, experiment, approved, "机械证据审计或双审未通过")
    connection.execute(
        "UPDATE nodes SET payload=? WHERE id=?", (json.dumps(payload), experiment["id"])
    )
    polarity = "supports" if approved else "refutes"
    connection.execute(
        "INSERT OR IGNORE INTO edges VALUES(?,?,?,?)",
        (experiment["id"], direction_id, polarity, now()),
    )
    _resolve_direction(connection, direction_id, approved)
    _register_review(connection, experiment["lineage_id"], approved)


def _resolve_direction(connection, node_id, approved) -> None:
    state = "supported" if approved else "refuted"
    connection.execute(
        "UPDATE nodes SET direction_status=CASE WHEN direction_status='proposed' "
        "THEN ? ELSE direction_status END,working=0,updated_at=? WHERE id=?",
        (state, now(), node_id),
    )


def _register_review(connection, lineage_id, approved) -> dict:
    lineage = _lineage(connection, lineage_id)
    streak = 0 if approved else lineage["rejection_streak"] + 1
    paused = int(streak >= 2)
    connection.execute(
        "UPDATE lineages SET rejection_streak=?,auto_paused=? WHERE id=?",
        (streak, paused, lineage_id),
    )
    return {**lineage, "rejection_streak": streak, "auto_paused": paused}


def _lineage(connection, lineage_id) -> dict:
    row = connection.execute(
        "SELECT * FROM lineages WHERE id=?", (lineage_id,)
    ).fetchone()
    return decode(row)

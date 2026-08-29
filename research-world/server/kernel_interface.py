from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .artifacts import ArtifactIntegrityError, ArtifactStore, now

__all__ = [
    "Artifact",
    "KernelInterface",
    "LocalMap",
    "LocalMapQuery",
    "Message",
    "Project",
    "Record",
    "Relation",
    "Session",
    "create_kernel",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kernel_projects(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  question TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kernel_sessions(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kernel_messages(
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES kernel_sessions(id) ON DELETE CASCADE,
  sequence INTEGER NOT NULL,
  content TEXT NOT NULL,
  assistant_response TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(session_id, sequence)
);
CREATE TABLE IF NOT EXISTS kernel_records(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK(type IN ('question','source','direction','experiment')),
  content TEXT NOT NULL,
  artifact_ids TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(project_id, id)
);
CREATE TABLE IF NOT EXISTS kernel_relations(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES kernel_projects(id) ON DELETE CASCADE,
  source_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('supports','refutes','depends_on')),
  created_at TEXT NOT NULL,
  UNIQUE(project_id, source_id, target_id, type),
  FOREIGN KEY(project_id, source_id)
    REFERENCES kernel_records(project_id, id) ON DELETE CASCADE,
  FOREIGN KEY(project_id, target_id)
    REFERENCES kernel_records(project_id, id) ON DELETE CASCADE
)
"""


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str
    question: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Message:
    id: str
    content: str
    assistant_response: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    project_id: str
    sha256: str
    media_type: str
    size: int
    created_at: str


@dataclass(frozen=True, slots=True)
class Record:
    id: str
    project_id: str
    type: str
    content: dict
    artifact_ids: tuple[str, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class Relation:
    id: str
    project_id: str
    source_id: str
    target_id: str
    type: str
    created_at: str


@dataclass(frozen=True, slots=True)
class LocalMapQuery:
    text: str | None = None
    record_id: str | None = None
    limit: int = 20


@dataclass(frozen=True, slots=True)
class LocalMap:
    records: tuple[Record, ...]
    relations: tuple[Relation, ...]
    artifacts: tuple[Artifact, ...]


@dataclass(frozen=True, slots=True)
class Session:
    id: str
    project_id: str
    title: str
    created_at: str
    messages: tuple[Message, ...]


class KernelInterface(Protocol):
    def create_project(self, name: str, question: str) -> Project: ...

    def get_project(self, project_id: str) -> Project: ...

    def list_projects(self) -> list[Project]: ...

    def create_session(self, project_id: str, title: str = "") -> Session: ...

    def get_session(self, project_id: str, session_id: str) -> Session: ...

    def list_sessions(self, project_id: str) -> list[Session]: ...

    def append_user_message(
        self,
        project_id: str,
        session_id: str,
        content: str,
        message_id: str | None = None,
    ) -> Message: ...

    def project_assistant_response(
        self, project_id: str, session_id: str, message_id: str, content: str
    ) -> Message: ...

    def capture_artifact(
        self, project_id: str, content: bytes, media_type: str
    ) -> Artifact: ...

    def get_artifact(self, project_id: str, artifact_id: str) -> Artifact: ...

    def read_artifact(self, project_id: str, artifact_id: str) -> bytes: ...

    def record(
        self,
        project_id: str,
        record_type: str,
        content: dict,
        artifact_ids: tuple[str, ...] = (),
    ) -> Record: ...

    def get_record(self, project_id: str, record_id: str) -> Record: ...

    def list_records(self, project_id: str) -> list[Record]: ...

    def remove_record(self, project_id: str, record_id: str) -> None: ...

    def connect(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
    ) -> Relation: ...

    def get_relation(self, project_id: str, relation_id: str) -> Relation: ...

    def list_relations(self, project_id: str) -> list[Relation]: ...

    def remove_relation(self, project_id: str, relation_id: str) -> None: ...

    def local_map(self, project_id: str, query: LocalMapQuery) -> LocalMap: ...


def create_kernel(database: Path, artifacts: Path) -> KernelInterface:
    return _SQLiteKernel(database, artifacts)


class _SQLiteKernel(KernelInterface):
    def __init__(self, database: Path, artifacts: Path):
        self._database = Path(database)
        self._artifacts = Path(artifacts)
        self._database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_project(self, name: str, question: str) -> Project:
        _require_text(name, "project name")
        _require_text(question, "project question")
        project = Project(_new_id("project"), name.strip(), question.strip(), now())
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO kernel_projects VALUES(?,?,?,?)",
                    (project.id, project.name, project.question, project.created_at),
                )
        except sqlite3.IntegrityError:
            raise ValueError("project name already exists") from None
        return project

    def get_project(self, project_id: str) -> Project:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id,name,question,created_at FROM kernel_projects WHERE id=?",
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return Project(*row)

    def list_projects(self) -> list[Project]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id,name,question,created_at FROM kernel_projects ORDER BY created_at,id"
            ).fetchall()
        return [Project(*row) for row in rows]

    def create_session(self, project_id: str, title: str = "") -> Session:
        self.get_project(project_id)
        if not isinstance(title, str):
            raise ValueError("session title must be text")
        session = Session(_new_id("session"), project_id, title.strip(), now(), ())
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO kernel_sessions VALUES(?,?,?,?)",
                (session.id, session.project_id, session.title, session.created_at),
            )
        return session

    def get_session(self, project_id: str, session_id: str) -> Session:
        self.get_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id,project_id,title,created_at FROM kernel_sessions WHERE id=?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise KeyError(session_id)
            if row["project_id"] != project_id:
                raise PermissionError("session belongs to another project")
            return _session_from_row(connection, row)

    def list_sessions(self, project_id: str) -> list[Session]:
        self.get_project(project_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id,project_id,title,created_at FROM kernel_sessions "
                "WHERE project_id=? ORDER BY created_at,id",
                (project_id,),
            ).fetchall()
            return [_session_from_row(connection, row) for row in rows]

    def append_user_message(
        self,
        project_id: str,
        session_id: str,
        content: str,
        message_id: str | None = None,
    ) -> Message:
        self.get_session(project_id, session_id)
        _require_text(content, "user message")
        message_id = message_id if message_id is not None else _new_id("message")
        _require_text(message_id, "message id")
        message = Message(message_id, content, None, now())
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            return _append_message(connection, session_id, message)

    def project_assistant_response(
        self, project_id: str, session_id: str, message_id: str, content: str
    ) -> Message:
        self.get_session(project_id, session_id)
        _require_text(content, "assistant response")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = _message_row(connection, message_id)
            if row is None:
                raise KeyError(message_id)
            if row["session_id"] != session_id:
                raise PermissionError("message belongs to another session")
            return _project_message(connection, row, content)

    def capture_artifact(
        self, project_id: str, content: bytes, media_type: str
    ) -> Artifact:
        self.get_project(project_id)
        if not isinstance(content, bytes):
            raise TypeError("artifact content must be bytes")
        _require_text(media_type, "artifact media type")
        try:
            record = ArtifactStore(self._artifacts, project_id).add(
                content, media_type.strip()
            )
        except ArtifactIntegrityError:
            raise ValueError("artifact operation failed") from None
        return _artifact_from_record(record)

    def get_artifact(self, project_id: str, artifact_id: str) -> Artifact:
        self.get_project(project_id)
        try:
            record = ArtifactStore(self._artifacts, project_id).get(artifact_id)
        except ArtifactIntegrityError:
            raise ValueError("artifact operation failed") from None
        return _artifact_from_record(record)

    def read_artifact(self, project_id: str, artifact_id: str) -> bytes:
        self.get_artifact(project_id, artifact_id)
        try:
            return ArtifactStore(self._artifacts, project_id).read(artifact_id)
        except ArtifactIntegrityError:
            raise ValueError("artifact operation failed") from None

    def record(
        self,
        project_id: str,
        record_type: str,
        content: dict,
        artifact_ids: tuple[str, ...] = (),
    ) -> Record:
        self.get_project(project_id)
        _validate_record(record_type, content, artifact_ids)
        for artifact_id in artifact_ids:
            self.get_artifact(project_id, artifact_id)
        value = _new_record(project_id, record_type, content, artifact_ids)
        self._insert_record(value)
        return value

    def _insert_record(self, record: Record) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO kernel_records VALUES(?,?,?,?,?,?)",
                _record_values(record),
            )

    def get_record(self, project_id: str, record_id: str) -> Record:
        self.get_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM kernel_records WHERE id=?", (record_id,)
            ).fetchone()
        if row is None:
            raise KeyError(record_id)
        if row["project_id"] != project_id:
            raise PermissionError("record belongs to another project")
        return _record_from_row(row)

    def list_records(self, project_id: str) -> list[Record]:
        self.get_project(project_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM kernel_records WHERE project_id=? "
                "ORDER BY created_at,id",
                (project_id,),
            ).fetchall()
        return list(map(_record_from_row, rows))

    def remove_record(self, project_id: str, record_id: str) -> None:
        self.get_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT project_id FROM kernel_records WHERE id=?", (record_id,)
            ).fetchone()
            _require_owned(row, record_id, project_id, "record")
            connection.execute(
                "DELETE FROM kernel_records WHERE project_id=? AND id=?",
                (project_id, record_id),
            )

    def connect(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
    ) -> Relation:
        if relation_type not in {"supports", "refutes", "depends_on"}:
            raise ValueError("invalid relation type")
        self.get_record(project_id, source_id)
        self.get_record(project_id, target_id)
        relation = _new_relation(project_id, source_id, target_id, relation_type)
        try:
            self._insert_relation(relation)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                raise
            raise ValueError("relation already exists") from None
        return relation

    def _insert_relation(self, relation: Relation) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO kernel_relations VALUES(?,?,?,?,?,?)",
                _relation_values(relation),
            )

    def get_relation(self, project_id: str, relation_id: str) -> Relation:
        self.get_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM kernel_relations WHERE id=?", (relation_id,)
            ).fetchone()
        if row is None:
            raise KeyError(relation_id)
        if row["project_id"] != project_id:
            raise PermissionError("relation belongs to another project")
        return _relation_from_row(row)

    def list_relations(self, project_id: str) -> list[Relation]:
        self.get_project(project_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM kernel_relations WHERE project_id=? "
                "ORDER BY created_at,id",
                (project_id,),
            ).fetchall()
        return list(map(_relation_from_row, rows))

    def remove_relation(self, project_id: str, relation_id: str) -> None:
        self.get_relation(project_id, relation_id)
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM kernel_relations WHERE project_id=? AND id=?",
                (project_id, relation_id),
            )

    def local_map(self, project_id: str, query: LocalMapQuery) -> LocalMap:
        self.get_project(project_id)
        _validate_local_map_query(query)
        records = _local_map_records(self, project_id, query)
        relations = _local_map_relations(self, project_id, records)
        artifacts = _local_map_artifacts(self, project_id, records)
        return LocalMap(records, relations, artifacts)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection


def _new_id(kind: str) -> str:
    return f"{kind}:{secrets.token_hex(12)}"


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")


def _require_owned(row, value_id: str, project_id: str, label: str) -> None:
    if row is None:
        raise KeyError(value_id)
    if row["project_id"] != project_id:
        raise PermissionError(f"{label} belongs to another project")


def _validate_record(record_type: str, content: dict, artifact_ids: tuple) -> None:
    if record_type not in {"question", "source", "direction", "experiment"}:
        raise ValueError("invalid record type")
    if not isinstance(content, dict) or not content:
        raise ValueError("record content must be a non-empty object")
    if not isinstance(artifact_ids, tuple) or not all(
        isinstance(value, str) for value in artifact_ids
    ):
        raise ValueError("record artifact ids must be a unique tuple")
    if len(set(artifact_ids)) != len(artifact_ids):
        raise ValueError("record artifact ids must be a unique tuple")
    try:
        json.dumps(content)
    except (TypeError, ValueError):
        raise ValueError("record content must be JSON serializable") from None


def _validate_local_map_query(query: LocalMapQuery) -> None:
    if not isinstance(query, LocalMapQuery):
        raise TypeError("local map query must be a LocalMapQuery")
    has_text = isinstance(query.text, str) and bool(query.text.strip())
    has_record = isinstance(query.record_id, str) and bool(query.record_id.strip())
    if has_text == has_record:
        raise ValueError("local map query requires text or record id")
    if isinstance(query.limit, bool) or not isinstance(query.limit, int) or query.limit < 1:
        raise ValueError("local map limit must be a positive integer")


def _record_matches(record: Record, text: str | None) -> bool:
    return text.strip().casefold() in _content_text(record.content).casefold()


def _content_text(value) -> str:
    if isinstance(value, dict):
        return " ".join(_content_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_content_text(item) for item in value)
    return str(value) if value is not None else ""


def _local_map_records(kernel, project_id: str, query: LocalMapQuery) -> tuple[Record, ...]:
    if isinstance(query.record_id, str) and query.record_id.strip():
        return (kernel.get_record(project_id, query.record_id),)
    records = kernel.list_records(project_id)
    return tuple(record for record in records if _record_matches(record, query.text))[
        : query.limit
    ]


def _local_map_relations(kernel, project_id: str, records: tuple[Record, ...]) -> tuple[Relation, ...]:
    ids = {record.id for record in records}
    return tuple(
        relation
        for relation in kernel.list_relations(project_id)
        if relation.source_id in ids or relation.target_id in ids
    )


def _local_map_artifacts(kernel, project_id: str, records: tuple[Record, ...]) -> tuple[Artifact, ...]:
    ids = dict.fromkeys(
        artifact_id for record in records for artifact_id in record.artifact_ids
    )
    return tuple(kernel.get_artifact(project_id, artifact_id) for artifact_id in ids)


def _new_record(project_id, record_type, content, artifact_ids) -> Record:
    return Record(
        _new_id("record"), project_id, record_type, content, artifact_ids, now()
    )


def _new_relation(project_id, source_id, target_id, relation_type) -> Relation:
    return Relation(
        _new_id("relation"),
        project_id,
        source_id,
        target_id,
        relation_type,
        now(),
    )


def _record_values(record: Record) -> tuple:
    return (
        record.id,
        record.project_id,
        record.type,
        json.dumps(record.content),
        json.dumps(record.artifact_ids),
        record.created_at,
    )


def _record_from_row(row: sqlite3.Row) -> Record:
    return Record(
        row["id"],
        row["project_id"],
        row["type"],
        json.loads(row["content"]),
        tuple(json.loads(row["artifact_ids"])),
        row["created_at"],
    )


def _relation_from_row(row: sqlite3.Row) -> Relation:
    return Relation(
        row["id"],
        row["project_id"],
        row["source_id"],
        row["target_id"],
        row["type"],
        row["created_at"],
    )


def _relation_values(relation: Relation) -> tuple:
    return (
        relation.id,
        relation.project_id,
        relation.source_id,
        relation.target_id,
        relation.type,
        relation.created_at,
    )


def _session_from_row(connection: sqlite3.Connection, row: sqlite3.Row) -> Session:
    messages = connection.execute(
        "SELECT id,content,assistant_response,created_at FROM kernel_messages "
        "WHERE session_id=? ORDER BY sequence",
        (row["id"],),
    ).fetchall()
    return Session(
        row["id"],
        row["project_id"],
        row["title"],
        row["created_at"],
        tuple(map(_message_from_row, messages)),
    )


def _message_from_row(row: sqlite3.Row) -> Message:
    return Message(
        row["id"], row["content"], row["assistant_response"], row["created_at"]
    )


def _message_row(connection: sqlite3.Connection, message_id: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT id,session_id,content,assistant_response,created_at "
        "FROM kernel_messages WHERE id=?",
        (message_id,),
    ).fetchone()


def _append_message(
    connection: sqlite3.Connection, session_id: str, message: Message
) -> Message:
    row = _message_row(connection, message.id)
    if row is not None:
        return _reuse_message(row, session_id, message.content)
    sequence = connection.execute(
        "SELECT COALESCE(MAX(sequence), -1) + 1 FROM kernel_messages WHERE session_id=?",
        (session_id,),
    ).fetchone()[0]
    connection.execute(
        "INSERT INTO kernel_messages "
        "(id,session_id,sequence,content,assistant_response,created_at) VALUES(?,?,?,?,?,?)",
        (message.id, session_id, sequence, message.content, None, message.created_at),
    )
    return message


def _project_message(
    connection: sqlite3.Connection, row: sqlite3.Row, content: str
) -> Message:
    if row["assistant_response"] is not None:
        if row["assistant_response"] != content:
            raise ValueError("assistant response is already projected")
        return _message_from_row(row)
    connection.execute(
        "UPDATE kernel_messages SET assistant_response=? WHERE id=?",
        (content, row["id"]),
    )
    return Message(row["id"], row["content"], content, row["created_at"])


def _reuse_message(row: sqlite3.Row, session_id: str, content: str) -> Message:
    if row["session_id"] != session_id or row["content"] != content:
        raise ValueError("message id already belongs to another message")
    return _message_from_row(row)


def _artifact_from_record(record: dict) -> Artifact:
    return Artifact(
        record["id"],
        record["project_id"],
        record["sha256"],
        record["media_type"],
        record["size"],
        record["created_at"],
    )

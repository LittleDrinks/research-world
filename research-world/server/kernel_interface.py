from __future__ import annotations

import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .artifacts import ArtifactIntegrityError, ArtifactStore, now

__all__ = [
    "Artifact",
    "KernelInterface",
    "Message",
    "Project",
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

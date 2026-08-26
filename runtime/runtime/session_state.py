from __future__ import annotations

import json
import os
from pathlib import Path


class SessionStateStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)

    def create(self, session_id: str, data: dict) -> None:
        path = self.path(session_id)
        if path.exists():
            raise ValueError(f"session state already exists: {session_id}")
        _write_private(path, data)

    def read(self, session_id: str) -> dict:
        return json.loads(self.path(session_id).read_text())

    def update(self, session_id: str, values: dict) -> None:
        _replace_private(self.path(session_id), {**self.read(session_id), **values})

    def path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.json"


def _write_private(path: Path, data: dict) -> None:
    payload = json.dumps(data, separators=(",", ":")).encode()
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def _replace_private(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    payload = json.dumps(data, separators=(",", ":")).encode()
    descriptor = os.open(temporary, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)

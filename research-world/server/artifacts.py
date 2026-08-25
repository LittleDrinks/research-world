from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def now() -> str:
    return datetime.now(UTC).isoformat()


class ArtifactIntegrityError(ValueError):
    def __init__(self, code: str, artifact_id: str):
        super().__init__(f"{code}: {artifact_id}")
        self.code = code
        self.artifact_id = artifact_id


class ArtifactStore:
    def __init__(self, root: Path, project_id: str):
        scope = hashlib.sha256(project_id.encode("utf-8")).hexdigest()
        self.project_id = project_id
        self.root = root / scope

    def add(self, content: bytes, media_type: str) -> dict:
        digest = hashlib.sha256(content).hexdigest()
        artifact_id = f"artifact:{digest}"
        path = self._content_path(digest)
        self._write_once(path, content)
        self._verify_content(artifact_id, path.read_bytes())
        record = self._register(artifact_id, media_type, len(content))
        return {**record, "path": str(self._content_path(digest))}

    def get(self, artifact_id: str) -> dict:
        digest = self._digest(artifact_id)
        metadata = self._metadata_path(digest)
        if not metadata.exists():
            raise KeyError(artifact_id)
        record = self._read_metadata(metadata, artifact_id)
        if record.get("id") != artifact_id or record.get("sha256") != digest:
            raise ArtifactIntegrityError("metadata_mismatch", artifact_id)
        return {**record, "path": str(self._content_path(digest))}

    def read(self, artifact_id: str) -> bytes:
        record = self.get(artifact_id)
        content = Path(record["path"]).read_bytes()
        self._verify_content(artifact_id, content)
        if len(content) != record["size"]:
            raise ArtifactIntegrityError("size_mismatch", artifact_id)
        return content

    def all(self) -> list[dict]:
        if not self.root.is_dir():
            return []
        records = []
        for metadata in sorted(self.root.rglob("*.json")):
            records.append(self.get(f"artifact:{metadata.stem}"))
        return records

    def _register(self, artifact_id: str, media_type: str, size: int) -> dict:
        digest = self._digest(artifact_id)
        record = self._record(artifact_id, media_type, size)
        self._write_once(self._metadata_path(digest), _encode(record))
        stored = self.get(artifact_id)
        fields = ("id", "project_id", "sha256", "media_type", "size")
        if any(stored[field] != record[field] for field in fields):
            raise ArtifactIntegrityError("metadata_conflict", artifact_id)
        return {field: stored[field] for field in (*fields, "created_at")}

    def _record(self, artifact_id: str, media_type: str, size: int) -> dict:
        return {
            "id": artifact_id,
            "project_id": self.project_id,
            "sha256": self._digest(artifact_id),
            "media_type": media_type,
            "size": size,
            "created_at": now(),
        }

    def _verify_content(self, artifact_id: str, content: bytes) -> None:
        actual = hashlib.sha256(content).hexdigest()
        if actual != self._digest(artifact_id):
            raise ArtifactIntegrityError("content_hash_mismatch", artifact_id)

    def _content_path(self, digest: str) -> Path:
        return self.root / digest[:2] / digest

    def _metadata_path(self, digest: str) -> Path:
        return self._content_path(digest).with_suffix(".json")

    @staticmethod
    def _read_metadata(path: Path, artifact_id: str) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ArtifactIntegrityError("metadata_invalid", artifact_id) from error

    @staticmethod
    def _digest(artifact_id: str) -> str:
        prefix, separator, digest = artifact_id.partition(":")
        is_hex = all(character in "0123456789abcdef" for character in digest)
        if prefix != "artifact" or not separator or len(digest) != 64 or not is_hex:
            raise KeyError(artifact_id)
        return digest

    @staticmethod
    def _write_once(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as target:
                target.write(content)
        except FileExistsError:
            pass


def _encode(value: dict) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")

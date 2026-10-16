from __future__ import annotations

import re
from datetime import datetime

ALLOWED_KEYS = {
    "kind",
    "payload",
    "provenance",
    "observed_at",
    "artifact_ids",
    "parent_id",
}
REQUIRED_KEYS = {"kind", "payload", "provenance", "observed_at", "artifact_ids"}
RESERVED_PAYLOAD_KEYS = {
    "provenance",
    "observed_at",
    "artifact_ids",
    "life_state",
    "direction_status",
    "working",
    "pipeline",
}
ARTIFACT_ID = re.compile(r"artifact:[0-9a-f]{64}\Z")


def observation_submission(value: dict) -> dict:
    _validate_fields(value)
    _validate_kind(value["kind"])
    payload = _payload(value["payload"])
    provenance = _provenance(value["provenance"])
    artifacts = _artifacts(value["artifact_ids"])
    command = {
        "kind": value["kind"],
        "payload": {
            **payload,
            "provenance": provenance,
            "observed_at": _timestamp(value["observed_at"]),
            "artifact_ids": artifacts,
        },
    }
    return _with_parent(command, value)


def _validate_fields(value: dict) -> None:
    if not isinstance(value, dict):
        raise TypeError("observation must be an object")
    if missing := REQUIRED_KEYS - set(value):
        raise ValueError(f"observation missing fields: {', '.join(sorted(missing))}")
    if unknown := set(value) - ALLOWED_KEYS:
        raise ValueError(f"observation rejects fields: {', '.join(sorted(unknown))}")


def _validate_kind(kind) -> None:
    if not isinstance(kind, str) or kind not in {"source", "experiment"}:
        raise ValueError("observation kind must be source or experiment")


def _payload(value) -> dict:
    if not isinstance(value, dict):
        raise TypeError("observation payload must be an object")
    if reserved := set(value) & RESERVED_PAYLOAD_KEYS:
        raise ValueError(
            f"observation payload rejects fields: {', '.join(sorted(reserved))}"
        )
    return dict(value)


def _provenance(value) -> dict:
    if not isinstance(value, dict):
        raise TypeError("observation provenance must be an object")
    for field in ("actor", "method"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"observation provenance requires {field}")
    return dict(value)


def _timestamp(value) -> str:
    if not isinstance(value, str):
        raise TypeError("observation observed_at must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("observation observed_at must be a timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("observation observed_at requires a timezone")
    return parsed.isoformat()


def _artifacts(value) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("observation artifact_ids must be a non-empty list")
    if not all(_artifact_id(item) for item in value) or len(set(value)) != len(value):
        raise ValueError("observation artifact_ids must be unique SHA-256 ids")
    return list(value)


def _artifact_id(value) -> bool:
    return isinstance(value, str) and ARTIFACT_ID.fullmatch(value) is not None


def _with_parent(command: dict, value: dict) -> dict:
    if "parent_id" not in value:
        return command
    if not _identifier(value["parent_id"]):
        raise ValueError("observation parent_id must be non-empty text")
    command["parent_id"] = value["parent_id"]
    return command


def _identifier(value) -> bool:
    return isinstance(value, str) and bool(value.strip())

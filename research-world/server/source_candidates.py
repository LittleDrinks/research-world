from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

FULL_TEXT_MEDIA = {
    "application/pdf",
    "application/vnd.jats+xml",
    "application/xml",
    "text/html",
    "text/markdown",
    "text/plain",
    "text/xml",
}
TEXT_SCHEMA = {"type": "string", "minLength": 1}

SOURCE_CANDIDATE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "title", "authors", "year", "venue", "source_type", "license",
        "access_status", "artifact", "relationship", "retrieval",
        "unresolved_questions",
    ],
    "properties": {
        "title": TEXT_SCHEMA,
        "authors": {"type": "array", "minItems": 1, "items": TEXT_SCHEMA},
        "year": {"type": "integer", "minimum": 1000, "maximum": 9999},
        "venue": TEXT_SCHEMA,
        "doi": TEXT_SCHEMA,
        "url": TEXT_SCHEMA,
        "source_type": TEXT_SCHEMA,
        "license": TEXT_SCHEMA,
        "access_status": {
            "enum": ["open", "restricted", "unknown", "full_text_unavailable"]
        },
        "artifact": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "project_file", "media_type", "sha256"],
                    "properties": {
                        "id": {"type": "string", "pattern": "^artifact:[0-9a-f]{64}$"},
                        "project_file": TEXT_SCHEMA,
                        "media_type": TEXT_SCHEMA,
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                },
            ]
        },
        "relationship": {
            "type": "object",
            "additionalProperties": False,
            "required": ["direction_id", "use", "relevance", "claims", "locations"],
            "properties": {
                "direction_id": {"type": "string", "pattern": "^node:[0-9a-f]+$"},
                "use": {"enum": ["supports", "refutes", "background"]},
                "relevance": TEXT_SCHEMA,
                "claims": {"type": "array", "items": TEXT_SCHEMA},
                "locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["locator", "quote"],
                        "properties": {"locator": TEXT_SCHEMA, "quote": TEXT_SCHEMA},
                    },
                },
            },
        },
        "retrieval": {
            "type": "object",
            "additionalProperties": False,
            "required": ["query", "database", "verified_at"],
            "properties": {
                "query": TEXT_SCHEMA,
                "database": TEXT_SCHEMA,
                "verified_at": TEXT_SCHEMA,
            },
        },
        "unresolved_questions": {"type": "array", "items": TEXT_SCHEMA},
    },
    "anyOf": [{"required": ["doi"]}, {"required": ["url"]}],
}


def validate_source_candidates(value) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError("runtime field 'source_candidates' must be a non-empty list")
    return [validate_source_candidate(candidate) for candidate in value]


def validate_source_candidate(value) -> dict:
    errors = sorted(
        Draft202012Validator(SOURCE_CANDIDATE_SCHEMA).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        raise ValueError(f"invalid SourceCandidate: {errors[0].message}")
    candidate = deepcopy(value)
    _validate_text(candidate)
    _validate_source(candidate)
    _validate_evidence_rule(candidate)
    return candidate


def validate_candidate_artifact(candidate, store, workspace: Path) -> None:
    artifact = candidate["artifact"]
    if artifact is None:
        return
    record = store.get(artifact["id"])
    store.read(artifact["id"])
    expected = {"sha256": artifact["sha256"], "media_type": artifact["media_type"]}
    if any(record[field] != value for field, value in expected.items()):
        raise ValueError("SourceCandidate Artifact metadata does not match Project Artifact")
    _validate_project_file(workspace, artifact)


def _validate_text(value) -> None:
    for text in _text_values(value):
        if not text.strip():
            raise ValueError("SourceCandidate text fields must not be blank")


def _text_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _text_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _text_values(child)
    elif isinstance(value, str):
        yield value


def _validate_source(candidate: dict) -> None:
    if "url" in candidate:
        parsed = urlsplit(candidate["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("SourceCandidate url must be a stable HTTP URL")
    try:
        datetime.fromisoformat(candidate["retrieval"]["verified_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("SourceCandidate verified_at must be ISO 8601") from error


def _validate_evidence_rule(candidate: dict) -> None:
    unavailable = candidate["access_status"] == "full_text_unavailable"
    relation = candidate["relationship"]
    if unavailable and (candidate["artifact"] is not None or relation["use"] != "background"):
        raise ValueError("full_text_unavailable sources require no Artifact and background use")
    if unavailable and relation["claims"]:
        raise ValueError("full_text_unavailable sources cannot support claims")
    if not unavailable and candidate["artifact"] is None:
        raise ValueError("full-text sources require an Artifact")
    if relation["use"] in {"supports", "refutes"} and not all(
        (relation["claims"], relation["locations"])
    ):
        raise ValueError("supports/refutes require claims and full-text locations")


def _validate_project_file(workspace: Path, artifact: dict) -> None:
    root = Path(workspace).resolve()
    path = (root / artifact["project_file"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("SourceCandidate Project File is outside the Project or missing")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact["sha256"]:
        raise ValueError("SourceCandidate Project File does not match Artifact SHA-256")
    if artifact["media_type"] not in FULL_TEXT_MEDIA:
        raise ValueError("SourceCandidate Artifact is not a supported full-text media type")

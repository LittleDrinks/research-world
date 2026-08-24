from __future__ import annotations

import hashlib
import json
from typing import Any

from jsonschema import ValidationError, validate

INPUT_FIELDS = ("image", "command", "files", "seed", "limits")
OUTPUT_FIELDS = ("exit_code", "stdout", "stderr")
INPUT_SCHEMA = {
    "type": "object",
    "required": list(INPUT_FIELDS),
    "additionalProperties": False,
    "properties": {
        "image": {"type": "string", "minLength": 1},
        "command": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "files": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "seed": {"type": "integer"},
        "limits": {
            "type": "object",
            "required": ["cpus", "memory_mb", "pids", "wall_seconds"],
            "additionalProperties": False,
            "properties": {
                "cpus": {"type": "number", "exclusiveMinimum": 0},
                "memory_mb": {"type": "integer", "minimum": 1},
                "pids": {"type": "integer", "minimum": 1},
                "wall_seconds": {"type": "integer", "minimum": 1},
            },
        },
    },
}
OUTPUT_SCHEMA = {
    "type": "object",
    "required": list(OUTPUT_FIELDS),
    "additionalProperties": False,
    "properties": {
        "exit_code": {"type": "integer"},
        "stdout": {"type": "string"},
        "stderr": {"type": "string"},
    },
}


def canonical_json(value: Any) -> bytes:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text.encode("utf-8")


def content_hash(value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value)).hexdigest()
    return f"sha256:{digest}"


def normalize_input(spec: dict) -> dict:
    value = {**spec, "files": spec.get("files", {}), "seed": spec.get("seed", 0)}
    _validate(value, INPUT_SCHEMA)
    limits = {
        **value["limits"],
        "cpus": float(value["limits"]["cpus"]),
    }
    return {
        **value,
        "command": list(value["command"]),
        "files": dict(sorted(value["files"].items())),
        "limits": limits,
    }


def normalize_output(result: dict) -> dict:
    value = {
        "exit_code": result["exit_code"],
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }
    _validate(value, OUTPUT_SCHEMA)
    return value


def build_evidence(spec: dict, result: dict) -> dict:
    execution_input = normalize_input(spec)
    credential = {**execution_input, **normalize_output(result)}
    evidence = {
        **credential,
        "input_hash": content_hash(execution_input),
        "content_hash": content_hash(credential),
    }
    return _with_usage(evidence, result)


def verify_evidence(evidence: dict) -> dict:
    try:
        execution_input = normalize_input(_select(evidence, INPUT_FIELDS))
        credential = {**execution_input, **normalize_output(evidence)}
    except (KeyError, TypeError, ValueError) as error:
        return failure("invalid_evidence", detail=str(error))
    input_check = _hash_check("input_hash", execution_input, evidence)
    return (
        input_check
        if not input_check["ok"]
        else _hash_check("content_hash", credential, evidence)
    )


def compare_replay(expected: dict, actual: dict) -> dict:
    for label, evidence in (("expected", expected), ("actual", actual)):
        check = verify_evidence(evidence)
        if not check["ok"]:
            return {**check, "code": f"{label}_{check['code']}"}
    if expected["input_hash"] != actual["input_hash"]:
        return mismatch("input_mismatch", expected, actual, "input_hash")
    if expected["content_hash"] != actual["content_hash"]:
        return mismatch("content_mismatch", expected, actual, "content_hash")
    return {"ok": True, "code": "match", "content_hash": actual["content_hash"]}


def credential_content(evidence: dict) -> bytes:
    check = verify_evidence(evidence)
    if not check["ok"]:
        raise ValueError(check["code"])
    execution_input = normalize_input(_select(evidence, INPUT_FIELDS))
    return canonical_json({**execution_input, **normalize_output(evidence)})


def persist_evidence_artifact(evidence: dict, store) -> str:
    record = store.add(
        credential_content(evidence),
        "application/vnd.research-world.execution+json",
    )
    expected = _artifact_id(evidence["content_hash"])
    if record["id"] != expected:
        raise ValueError("execution artifact hash mismatch")
    return record["id"]


def verify_evidence_artifact(evidence: dict, artifact_id: str, store) -> dict:
    check = verify_evidence(evidence)
    if not check["ok"]:
        return check
    if artifact_id != _artifact_id(evidence["content_hash"]):
        return failure("artifact_reference_mismatch")
    try:
        content = store.read(artifact_id)
    except (KeyError, ValueError) as error:
        return failure("artifact_integrity_failure", detail=str(error))
    return (
        {"ok": True, "code": "verified"}
        if content == credential_content(evidence)
        else failure("artifact_content_mismatch")
    )


def failure(code: str, **details: Any) -> dict:
    return {"ok": False, "code": code, **details}


def mismatch(code: str, expected: dict, actual: dict, field: str) -> dict:
    return failure(
        code,
        expected_hash=expected[field],
        actual_hash=actual[field],
    )


def _hash_check(field: str, value: dict, evidence: dict) -> dict:
    expected = content_hash(value)
    actual = evidence.get(field)
    if actual == expected:
        return {"ok": True, "code": "verified", field: actual}
    return failure(f"{field}_mismatch", expected_hash=expected, actual_hash=actual)


def _validate(value: dict, schema: dict) -> None:
    try:
        validate(value, schema)
    except ValidationError as error:
        path = ".".join(str(item) for item in error.absolute_path)
        prefix = f"{path}: " if path else ""
        raise ValueError(f"{prefix}{error.message}") from error


def _with_usage(evidence: dict, result: dict) -> dict:
    if "usage" in result:
        evidence["usage"] = result["usage"]
    return evidence


def _select(value: dict, fields: tuple[str, ...]) -> dict:
    return {field: value[field] for field in fields}


def _artifact_id(content_digest: str) -> str:
    prefix, separator, digest = content_digest.partition(":")
    if prefix != "sha256" or not separator:
        raise ValueError("invalid execution content hash")
    return f"artifact:{digest}"

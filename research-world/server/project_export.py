from __future__ import annotations

import hashlib
import io
import json
import math
import re
import zipfile

_SECRET = {"apikey", "authorization", "clientsecret", "credential", "credentials", "password", "secret", "token", "tokens", "accesstoken", "refreshtoken", "idtoken", "bearertoken"}
_SECRET_TEXT = re.compile(r"(?ix)(?P<label>\b(?:api[^a-z0-9\r\n]*key|authorization|client[^a-z0-9\r\n]*secret|credentials?|password|secrets?|tokens?|access[^a-z0-9\r\n]*token|refresh[^a-z0-9\r\n]*token|id[^a-z0-9\r\n]*token|bearer[^a-z0-9\r\n]*token)\b\s*[:=]\s*)(?:[\"'][^\r\n]*?[\"']|[\[\(\{][^\r\n]*?[\]\)\}]|[^\r\n,;]+)")
_URL = re.compile(r"(https?://[^\s\"'<>]+)", re.I)
_PATH = re.compile(r"(?i)(?<![:\w/])/(?:[^/\r\n]+/)+[^\r\n]*|\b[a-z]:[\\/][^\r\n]*")


def package(project, graph, runs, traces, artifacts) -> bytes:
    files = _records(project, graph, runs, traces, artifacts)
    files["manifest.json"] = _json(_manifest(project["id"], files))
    return _archive(files)


def _records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    files = _facts(project, graph, runs, traces, artifacts)
    for artifact in artifacts:
        files[f"artifacts/{artifact['sha256']}"] = _json(_omission(artifact))
        if _bibtex(artifact):
            files[f"bibtex/{artifact['sha256']}.bib"] = _bibtex_record(artifact)
    return files


def _facts(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    return {
        "project.json": _json(_safe({"project": project, "graph": graph})),
        "pipeline-runs.json": _json(_safe(runs)),
        "traces.json": _json(_safe(traces)),
        "artifacts.json": _json(_safe([_metadata(item) for item in artifacts])),
    }


def _metadata(artifact) -> dict:
    keys = ("id", "sha256", "media_type", "size", "created_at")
    return {key: _safe(artifact[key], key) for key in keys}


def _omission(artifact) -> dict:
    return {"artifact": _metadata(artifact), "omitted": "raw_content"}


def _bibtex(artifact) -> bool:
    return artifact["media_type"].split(";", 1)[0].strip().lower() in {"application/x-bibtex", "text/x-bibtex"}


def _bibtex_record(artifact) -> bytes:
    return f"@comment{{artifact_sha256={artifact['sha256']}}}\n".encode()


def _safe(value, key="", seen=None):
    seen = set() if seen is None else seen
    if _secret_key(key):
        return "[REDACTED]"
    if isinstance(value, str):
        return _text(value)
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "[REDACTED]"
    return _container(value, seen)


def _container(value, seen):
    if not isinstance(value, (dict, list, tuple)) or id(value) in seen:
        return "[REDACTED]"
    seen.add(id(value))
    try:
        return _mapping(value, seen) if isinstance(value, dict) else [_safe(item, seen=seen) for item in value]
    finally:
        seen.remove(id(value))


def _mapping(value, seen):
    if not all(isinstance(key, str) for key in value):
        return "[REDACTED]"
    return {key: _safe(item, key, seen) for key, item in sorted(value.items())}


def _text(value: str) -> str:
    if _absolute(value):
        return "[REDACTED]"
    return "".join(_fragment(part) for part in _URL.split(value))


def _fragment(value: str) -> str:
    if _URL.fullmatch(value):
        return value
    return _PATH.sub("[REDACTED]", _SECRET_TEXT.sub(r"\g<label>[REDACTED]", value))


def _absolute(value: str) -> bool:
    return bool(re.fullmatch(r"/(?:[^/\r\n]+/)+[^\r\n]+|(?i:[a-z]:[\\/].+)", value))


def _secret_key(key: str) -> bool:
    return re.sub(r"[^a-z0-9]", "", key.lower()) in _SECRET


def _manifest(project_id, files) -> dict:
    return {"schema_version": 3, "project_id": _safe(project_id), "files": _checksums(files)}


def _checksums(files) -> list[dict]:
    return [{"path": path, "sha256": _sha256(content), "size": len(content)} for path, content in sorted(files.items())]


def _archive(files) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, content in sorted(files.items()):
            archive.writestr(_entry(path), content)
    return output.getvalue()


def _entry(path):
    entry = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
    entry.create_system, entry.external_attr = 3, 0o100600 << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    return entry


def _json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"


def _sha256(content) -> str:
    return hashlib.sha256(content).hexdigest()

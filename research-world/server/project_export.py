from __future__ import annotations

import hashlib
import io
import json
import math
import re
import zipfile
from collections.abc import Mapping
from urllib.parse import unquote_plus, urlsplit, urlunsplit

_SECRET = {"apikey", "authorization", "clientsecret", "credential", "credentials", "password", "secret", "token", "tokens", "accesstoken", "refreshtoken", "idtoken", "bearertoken"}
_SECRET_TEXT = re.compile(r"(?ix)(?P<label>\b(?:api[^a-z0-9\r\n]*key|authorization|client[^a-z0-9\r\n]*secret|credentials?|password|secrets?|tokens?|access[^a-z0-9\r\n]*token|refresh[^a-z0-9\r\n]*token|id[^a-z0-9\r\n]*token|bearer[^a-z0-9\r\n]*token)\b\s*[:=]\s*)(?:[\"'][^\r\n]*?[\"']|[\[\(\{][^\r\n]*?[\]\)\}]|[^\r\n,;]+)")
_URL = re.compile(r"(https?://[^\s\"'<>]+)", re.I)
_PATH = re.compile(r"(?i)(?<![:\w/])/(?:[^/\r\n]+/)*[^/\r\n]+|\b[a-z]:[\\/][^\r\n]*")
_MARK = "[REDACTED]"
_MAX_DEPTH = 64


def package(project, graph, runs, traces, artifacts) -> bytes:
    files = _records(project, graph, runs, traces, artifacts)
    files["manifest.json"] = _json(_manifest(project["id"], files))
    return _archive(files)


def _records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    files = _facts(project, graph, runs, traces, artifacts)
    for artifact in artifacts:
        digest = _member_digest(artifact)
        files[f"artifacts/{digest}"] = _json(_omission(artifact))
        if _bibtex(artifact):
            files[f"bibtex/{digest}.bib"] = _bibtex_record(digest)
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
    value = artifact["media_type"]
    return isinstance(value, str) and value.split(";", 1)[0].strip().lower() in {"application/x-bibtex", "text/x-bibtex"}


def _bibtex_record(digest) -> bytes:
    return f"@comment{{artifact_sha256={digest}}}\n".encode()


def _member_digest(artifact) -> str:
    digest = artifact.get("sha256")
    return digest if isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) else _sha256(_json(_metadata(artifact)))


def _safe(value, key=""):
    result = {}
    _walk(result, "value", value, key)
    return result["value"]


def _walk(parent, slot, value, key):
    stack = [(parent, slot, value, key, 0, ())]
    while stack:
        target, name, item, label, depth, ancestors = stack.pop()
        if _scalar(target, name, item, label):
            continue
        children = _children(item) if depth < _MAX_DEPTH and id(item) not in ancestors else None
        if children is None:
            _put(target, name, _MARK)
            continue
        result, values = children
        _put(target, name, result)
        lineage = ancestors + (id(item),)
        stack.extend((result, index, child, child_key, depth + 1, lineage) for index, child, child_key in reversed(values))


def _put(parent, slot, value):
    if isinstance(parent, list):
        parent.append(value)
    else:
        parent[slot] = value


def _scalar(parent, slot, value, key) -> bool:
    if _secret_key(key):
        _put(parent, slot, _MARK)
    elif isinstance(value, str):
        _put(parent, slot, _text(value))
    elif value is None or isinstance(value, (bool, int)):
        _put(parent, slot, value)
    elif isinstance(value, float):
        _put(parent, slot, value if math.isfinite(value) else _MARK)
    else:
        return False
    return True


def _children(value):
    if isinstance(value, Mapping):
        return _map_children(value)
    if isinstance(value, (list, tuple)):
        return [], [(index, item, "") for index, item in enumerate(value)]
    return None


def _map_children(value):
    try:
        values = [(_text(key), key, item) for key, item in value.items()]
    except (AttributeError, TypeError, ValueError):
        return None
    if any(not isinstance(key, str) or cleaned == _MARK for cleaned, key, _ in values):
        return None
    if len({cleaned for cleaned, _, _ in values}) != len(values):
        return None
    return {}, [(cleaned, item, key) for cleaned, key, item in sorted(values)]


def _text(value: str) -> str:
    if _absolute(value):
        return _MARK
    if value.lstrip().startswith(("{", "[")):
        return _serialized(value)
    return "".join(_fragment(part) for part in _URL.split(value))


def _fragment(value: str) -> str:
    if _URL.fullmatch(value):
        return _url(value)
    return _PATH.sub(_MARK, _SECRET_TEXT.sub(r"\g<label>[REDACTED]", value))


def _serialized(value):
    try:
        return _json(_safe(json.loads(value))).decode().rstrip()
    except (json.JSONDecodeError, RecursionError, TypeError, ValueError):
        return _MARK


def _url(value):
    parts = urlsplit(value)
    query = _query(parts.query)
    user, mark, host = parts.netloc.rpartition("@")
    if not mark and query == parts.query:
        return value
    netloc = f"{_MARK}@{host}" if mark else parts.netloc
    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))


def _query(value):
    parts = re.split(r"([&;])", value)
    return "".join(_query_part(part) if index % 2 == 0 else part for index, part in enumerate(parts))


def _query_part(value):
    key, separator, _value = value.partition("=")
    return f"{key}{separator}{_MARK}" if separator and _secret_key(unquote_plus(key)) else value


def _absolute(value: str) -> bool:
    return bool(re.fullmatch(r"/(?:[^/\r\n]+/)+[^\r\n]+|(?i:[a-z]:[\\/].+)", value))


def _secret_key(key: str) -> bool:
    return isinstance(key, str) and re.sub(r"[^a-z0-9]", "", key.lower()) in _SECRET


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

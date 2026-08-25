from __future__ import annotations

import hashlib
import io
import json
import math
import re
import zipfile
from urllib.parse import unquote_plus, urlsplit, urlunsplit

_ARTIFACT = re.compile(r"artifact:([0-9a-f]{64})\Z")
_DRIVE = re.compile(r"(?i)\b[a-z]:[\\/][^\r\n]*")
_PATH = re.compile(r"(?<![:\w/])/(?:[^/\r\n]+/)*[^/\r\n]+")
_SECRET = re.compile(r"(?ix)\b(api[^a-z0-9]*key|base[^a-z0-9]*url|authorization|client[^a-z0-9]*secret|credentials?|password|secrets?|tokens?|access[^a-z0-9]*token|refresh[^a-z0-9]*token|id[^a-z0-9]*token|bearer[^a-z0-9]*token)\b[^\r\n:=]*[:=]\s*[^\r\n]*")
_URI = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*:[^\s\"'<>]*")
_MARK = "[REDACTED]"
_MAX_BYTES = 1_000_000
_MAX_DEPTH = 64
_MAX_ITEMS = 10_000


def package(project, graph, runs, traces, artifacts) -> bytes:
    artifacts = _artifact_list(artifacts)
    files = _records(project, graph, runs, traces, artifacts)
    files["manifest.json"] = _json(_manifest(project.get("id"), files))
    return _archive(files)


def _records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    files = _facts(project, graph, runs, traces, artifacts)
    for artifact in artifacts:
        digest = _identity(artifact)
        if digest:
            _artifact_records(files, artifact, digest)
    return files


def _artifact_list(value):
    return value if isinstance(value, (list, tuple)) and len(value) <= _MAX_ITEMS else ()


def _facts(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    return {
        "project.json": _json(_safe({"project": project, "graph": graph})),
        "pipeline-runs.json": _json(_safe(runs)),
        "traces.json": _json(_safe(traces)),
        "artifacts.json": _json(_safe([_metadata(item) for item in artifacts])),
    }


def _artifact_records(files, artifact, digest) -> None:
    files[f"artifacts/{digest}"] = _json(_safe(_omission(artifact)))
    if _bibtex(artifact):
        files[f"bibtex/{digest}.bib"] = _bibtex_record(digest)


def _metadata(artifact) -> dict:
    digest = _identity(artifact)
    if not digest:
        return {"omitted": "invalid_artifact_identity"}
    keys = ("id", "sha256", "media_type", "size", "created_at")
    return {key: artifact[key] for key in keys}


def _identity(artifact) -> str | None:
    if not isinstance(artifact, dict):
        return None
    match = _ARTIFACT.fullmatch(artifact.get("id", ""))
    digest = artifact.get("sha256")
    return match.group(1) if match and digest == match.group(1) else None


def _omission(artifact) -> dict:
    return {"artifact": _metadata(artifact), "omitted": "raw_content"}


def _bibtex(artifact) -> bool:
    value = artifact.get("media_type") if isinstance(artifact, dict) else None
    return isinstance(value, str) and value.split(";", 1)[0].strip().lower() in {"application/x-bibtex", "text/x-bibtex"}


def _bibtex_record(digest) -> bytes:
    return f"@comment{{artifact_sha256={digest}}}\\n".encode()


def _safe(value, key=""):
    result = {}
    return result["value"] if _walk(result, "value", value, key) else _MARK


def _walk(parent, slot, value, key):
    stack, seen, count = [(parent, slot, value, key, 0)], set(), 0
    while stack:
        count += 1
        if count > _MAX_ITEMS:
            return False
        target, name, item, label, depth = stack.pop()
        if _scalar(target, name, item, label):
            continue
        if not _container(target, name, item, stack, seen, depth):
            _put(target, name, _MARK)
    return True


def _container(parent, slot, value, stack, seen, depth) -> bool:
    if depth >= _MAX_DEPTH or not isinstance(value, (dict, list, tuple)):
        return False
    if id(value) in seen or len(value) > _MAX_ITEMS:
        return False
    seen.add(id(value))
    if isinstance(value, dict):
        return _mapping(parent, slot, value, stack, depth)
    _put(parent, slot, [])
    _sequence(parent[slot], value, stack, depth)
    return True


def _mapping(parent, slot, value, stack, depth) -> bool:
    keys = sorted(value)
    if not all(isinstance(key, str) for key in keys):
        return False
    cleaned = [_clean_key(key) for key in keys]
    if len(set(cleaned)) != len(cleaned):
        return False
    result = {}
    _put(parent, slot, result)
    for index in range(len(keys) - 1, -1, -1):
        stack.append((result, cleaned[index], value[keys[index]], keys[index], depth + 1))
    return True


def _sequence(parent, value, stack, depth) -> None:
    for index in range(len(value) - 1, -1, -1):
        stack.append((parent, index, value[index], "", depth + 1))


def _put(parent, slot, value) -> None:
    if isinstance(parent, list):
        parent.append(value)
    else:
        parent[slot] = value


def _scalar(parent, slot, value, key) -> bool:
    if _secret_key(key) or (isinstance(key, str) and _clean_key(key) == _MARK):
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


def _text(value: str) -> str:
    if len(value.encode()) > _MAX_BYTES or _absolute(value):
        return _MARK
    if value.lstrip().startswith(("{", "[")):
        return _serialized(value)
    value = _SECRET.sub(_MARK, _uris(value))
    return _PATH.sub(_MARK, _DRIVE.sub(_MARK, value))


def _serialized(value: str) -> str:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, RecursionError):
        return _MARK
    safe = _safe(parsed)
    return _MARK if safe == _MARK else _json(safe).decode().rstrip()


def _uris(value: str) -> str:
    return _URI.sub(lambda match: _uri(match.group()), value)


def _uri(value: str) -> str:
    parts = urlsplit(value)
    netloc = _MARK if parts.username or parts.password else parts.netloc
    return urlunsplit((parts.scheme, netloc, parts.path, _query(parts.query), parts.fragment))


def _query(value: str) -> str:
    return re.sub(r"[^&;]+", lambda match: _query_part(match.group()), value)


def _query_part(value: str) -> str:
    key, mark, _content = value.partition("=")
    return f"{key}{mark}{_MARK}" if mark and _secret_key(unquote_plus(key)) else value


def _absolute(value: str) -> bool:
    return bool(re.fullmatch(r"/(?:[^/\r\n]+/)+[^\r\n]+|(?i:[a-z]:[\\/].+)", value))


def _secret_key(key: str) -> bool:
    cleaned = re.sub(r"[^a-z0-9]", "", key.lower()) if isinstance(key, str) else ""
    return cleaned in {"apikey", "baseurl", "authorization", "clientsecret", "credential", "credentials", "password", "secret", "token", "tokens", "accesstoken", "refreshtoken", "idtoken", "bearertoken"}


def _clean_key(key: str) -> str:
    return _MARK if _secret_key(key) else _text(key)


def _manifest(project_id, files) -> dict:
    return {"schema_version": 4, "project_id": _safe(project_id), "files": _checksums(files)}


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

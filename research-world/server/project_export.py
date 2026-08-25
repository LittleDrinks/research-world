from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile

_SECRET_FIELDS = {"api_key", "apikey", "authorization", "credential", "credentials", "password", "secret", "access_token", "refresh_token", "id_token", "bearer_token"}
_TEMPORARY_FIELD = re.compile(r"^(tmp|temp|temporary)(_|$)", re.I)
_SECRET_TEXT = re.compile(r"(?ix)(?P<label>\b(?:api[_ -]?key|authorization|credentials?|password|secrets?|access[_ -]?token|refresh[_ -]?token|id[_ -]?token|bearer[_ -]?token)\b[\"']?\s*[:=]\s*)(?:(?P<quote>[\"'])(?P<quoted>[^\r\n]*?)(?P=quote)|bearer\s+(?P<bearer>[^\s,;)}\]\"'<>]+)|(?P<plain>[^\s,;)}\]\"'<>]+))")
_POSIX_PATH = re.compile(r"(?<![:\w/])/[A-Za-z_.][A-Za-z0-9_.-]*(?:/[^\r\n,;)}\]\"'<>]+)+")
_WINDOWS_PATH = re.compile(r"(?i)\b[a-z]:\\[^\r\n,;)}\]\"'<>]+")
_URL = re.compile(r"(https?://[^\s\"'<>]+)", re.I)


def package(project: dict, graph: dict, runs: list[dict], traces: dict, artifacts: list[dict]) -> bytes:
    files = _records(project, graph, runs, traces, artifacts)
    files["manifest.json"] = _json(_manifest(project["id"], files))
    return _archive(files)


def _records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    values = _structured_records(project, graph, runs, traces, artifacts)
    for artifact in artifacts:
        exported = _export_artifact(artifact)
        values[f"artifacts/{artifact['sha256']}"] = exported["content"]
        if artifact.get("bibtex"):
            values[f"bibtex/{artifact['sha256']}.bib"] = exported["content"]
    return values


def _structured_records(project, graph, runs, traces, artifacts) -> dict[str, bytes]:
    exported = [_export_artifact(item) for item in artifacts]
    return {
        "project.json": _json(_clean({"project": project, "graph": graph})),
        "pipeline-runs.json": _json(_clean(runs)),
        "traces.json": _json(_clean(traces)),
        "artifacts.json": _json(_clean([_artifact_metadata(item) for item in exported])),
    }


def _export_artifact(artifact: dict) -> dict:
    content, redacted = _artifact_content(artifact)
    return {**artifact, "content": content, "redacted": redacted, "export_sha256": _sha256(content), "export_size": len(content)}


def _artifact_content(artifact: dict) -> tuple[bytes, bool]:
    content = artifact["content"]
    if not _textual(artifact["media_type"]):
        return content, False
    text = content.decode("utf-8", errors="replace")
    cleaned = _clean_text(text)
    return cleaned.encode(), cleaned != text


def _artifact_metadata(artifact: dict) -> dict:
    fields = ("id", "sha256", "media_type", "size", "created_at", "redacted", "export_sha256", "export_size")
    return {field: artifact[field] for field in fields}


def _textual(media_type: str) -> bool:
    bibtex = {"application/x-bibtex", "text/x-bibtex"}
    return media_type.startswith("text/") or media_type.endswith("+json") or media_type in bibtex | {"application/json"}


def _manifest(project_id: str, files: dict[str, bytes]) -> dict:
    return {"schema_version": 2, "project_id": project_id, "files": _checksums(files)}


def _checksums(files: dict[str, bytes]) -> list[dict]:
    return [{"path": path, "sha256": _sha256(content), "size": len(content)} for path, content in sorted(files.items())]


def _archive(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, content in sorted(files.items()):
            archive.writestr(_entry(path), content)
    return output.getvalue()


def _entry(path: str) -> zipfile.ZipInfo:
    entry = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
    entry.create_system, entry.external_attr = 3, 0o100600 << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    return entry


def _json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _clean(value, key: str = ""):
    if key.lower() in _SECRET_FIELDS or key == "root" or _TEMPORARY_FIELD.match(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {item: _clean(child, item) for item, child in sorted(value.items())}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    return _clean_text(value) if isinstance(value, str) else value


def _clean_text(value: str) -> str:
    return "".join(_clean_fragment(part) for part in _URL.split(value))


def _clean_fragment(value: str) -> str:
    if _URL.fullmatch(value):
        return _SECRET_TEXT.sub(_redact_secret, value)
    cleaned = _SECRET_TEXT.sub(_redact_secret, value)
    cleaned = _POSIX_PATH.sub("[REDACTED]", cleaned)
    return _WINDOWS_PATH.sub("[REDACTED]", cleaned)


def _redact_secret(match: re.Match) -> str:
    quote = match.group("quote")
    return f"{match.group('label')}{quote}[REDACTED]{quote}" if quote else f"{match.group('label')}[REDACTED]"

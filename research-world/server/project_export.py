from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from xml.etree import ElementTree

import yaml

_SECRET_FIELDS = {"api_key", "apikey", "authorization", "client_secret", "credential", "credentials", "password", "secret", "access_token", "refresh_token", "id_token", "bearer_token"}
_TEMPORARY_FIELD = re.compile(r"^(tmp|temp|temporary)(_|$)", re.I)
_SECRET_TEXT = re.compile(r"(?ix)(?P<label>\b(?:api[_ -]?key|authorization|client[_ -]?secret|credentials?|password|secrets?|access[_ -]?token|refresh[_ -]?token|id[_ -]?token|bearer[_ -]?token)\b[\"']?\s*[:=]\s*)(?:(?P<quote>[\"'])(?P<quoted>[^\r\n]*?)(?P=quote)|bearer\s+(?P<bearer>[^\s,;)}\]\"'<>]+)|(?P<plain>[^\s,;)}\]\"'<>]+))")
_POSIX_VALUE = re.compile(r"/[^/\r\n]+(?:/[^/\r\n]+)+")
_WINDOWS_VALUE = re.compile(r"(?i)[a-z]:\\[^\r\n]+")
_POSIX_PATH = re.compile(r"(?<![:\w/])/(?:[^\s/\\,;)}\]\"'<>]+/)+[^\s/\\,;)}\]\"'<>]+(?=$|[,;)}\]\"'<>])")
_WINDOWS_PATH = re.compile(r"(?i)\b[a-z]:\\[^\s,;)}\]\"'<>]+(?=$|[,;)}\]\"'<>])")
_QUOTED_PATH = re.compile(r"(?P<quote>[\"'])(?P<path>/(?:[^/\"'\r\n]+/)+[^/\"'\r\n]+|[a-z]:\\[^\"'\r\n]+)(?P=quote)", re.I)
_BRACKETED_PATH = re.compile(r"(?P<open>[\[(])(?P<path>/(?:[^/\]\)\r\n]+/)+[^/\]\)\r\n]+|[a-z]:\\[^\]\)\r\n]+)(?P<close>[\])])", re.I)
_URL = re.compile(r"(https?://[^\s\"'<>]+)", re.I)
_TEXTUAL_APPLICATION = {"application/json", "application/x-bibtex", "application/xml", "application/javascript", "application/yaml", "application/x-yaml"}


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
    cleaned = _clean_artifact_text(_media_type(artifact["media_type"]), text)
    return cleaned.encode(), cleaned != text


def _artifact_metadata(artifact: dict) -> dict:
    fields = ("id", "sha256", "media_type", "size", "created_at", "redacted", "export_sha256", "export_size")
    return {field: artifact[field] for field in fields}


def _textual(media_type: str) -> bool:
    media_type = _media_type(media_type)
    return media_type.startswith("text/") or media_type.endswith(("+json", "+xml")) or media_type in _TEXTUAL_APPLICATION


def _media_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _clean_artifact_text(media_type: str, text: str) -> str:
    if media_type == "application/json" or media_type.endswith("+json"):
        return _clean_json(text)
    if media_type == "application/xml" or media_type.endswith("+xml"):
        return _clean_xml(text)
    if media_type in {"application/yaml", "application/x-yaml"}:
        return _clean_yaml(text)
    return _clean_text(text)


def _clean_json(text: str) -> str:
    try:
        return _json(_clean(json.loads(text))).decode()
    except json.JSONDecodeError:
        return _clean_text(text)


def _clean_yaml(text: str) -> str:
    try:
        return yaml.safe_dump(_clean(yaml.safe_load(text)), allow_unicode=True, sort_keys=True)
    except yaml.YAMLError:
        return _clean_text(text)


def _clean_xml(text: str) -> str:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return _clean_text(text)
    _clean_xml_element(root)
    return ElementTree.tostring(root, encoding="unicode")


def _clean_xml_element(element) -> None:
    key = element.tag.rsplit("}", 1)[-1]
    element.text = _clean(element.text, key) if element.text else element.text
    element.attrib.update({name: _clean(value, name.rsplit("}", 1)[-1]) for name, value in element.attrib.items()})
    for child in element:
        _clean_xml_element(child)
        child.tail = _clean_text(child.tail) if child.tail else child.tail


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
    if _absolute_path(value):
        return "[REDACTED]"
    if cleaned := _clean_serialized_json(value):
        return cleaned
    return "".join(_clean_fragment(part) for part in _URL.split(value))


def _clean_fragment(value: str) -> str:
    if _URL.fullmatch(value):
        return _SECRET_TEXT.sub(_redact_secret, value)
    cleaned = _SECRET_TEXT.sub(_redact_secret, value)
    cleaned = _QUOTED_PATH.sub(_redact_path, cleaned)
    cleaned = _BRACKETED_PATH.sub(_redact_path, cleaned)
    cleaned = _POSIX_PATH.sub("[REDACTED]", cleaned)
    return _WINDOWS_PATH.sub("[REDACTED]", cleaned)


def _redact_secret(match: re.Match) -> str:
    quote = match.group("quote")
    return f"{match.group('label')}{quote}[REDACTED]{quote}" if quote else f"{match.group('label')}[REDACTED]"


def _absolute_path(value: str) -> bool:
    return bool(_POSIX_VALUE.fullmatch(value) or _WINDOWS_VALUE.fullmatch(value))


def _redact_path(match: re.Match) -> str:
    return f"{match.group('quote') or match.group('open')}[REDACTED]{match.group('quote') or match.group('close')}"


def _clean_serialized_json(value: str) -> str | None:
    for candidate, escaped in ((value, False), (value.replace(r'\"', '"'), True)):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        cleaned = _clean(parsed)
        rendered = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
        if cleaned != parsed:
            return rendered.replace('"', r'\"') if escaped else rendered
    return None
